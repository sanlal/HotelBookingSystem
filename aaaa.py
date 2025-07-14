"""
Not updated in availability rooms after checkout and remove paid option in user.

"""
import re
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'santhor1',
    'database': 'python_project'
}

class DBConnection:
    def connect(self):
        try:
            self.conn = mysql.connector.connect(**db_config)
            return self.conn
        except Error as e:
            print(f"Error connecting to database: {e}")
            exit(1)

    def get_cursor(self):
        if not self.conn or not self.conn.is_connected():
            self.connect()
        return self.conn.cursor()

    def commit(self):
        self.conn.commit()

class Admin:
    def __init__(self, conn, adminid, adminname):
        self.conn = conn
        self.adminid = adminid
        self.adminname = adminname

    def view_all_bookings(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT b.booking_id, u.username, r.room_no, b.check_in_date, b.check_out_date, b.amount, b.payment_status
            FROM booking b
            JOIN user u ON b.userid = u.userid
            JOIN room r ON b.room_no = r.room_no
        """)
        bookings = cur.fetchall()
        print("\n--- All Bookings ---")
        for b in bookings:
            print(f"ID: {b[0]}, User: {b[1]}, Room: {b[2]}, In: {b[3]}, Out: {b[4]}, Amount: ₹{b[5] or 0}, Status: {b[6]}")

    def add_room(self):
        try:
            rtype = input("Room type (Standard/Deluxe/Luxury): ").strip()
            rprice = int(input("Price per day: "))
            cur = self.conn.cursor()
            cur.execute("INSERT INTO room (room_type, room_price, is_avail) VALUES (%s, %s, TRUE)", (rtype, rprice))
            self.conn.commit()
            print("Room added.")
        except Exception as e:
            print(f"Failed: {e}")

    def update_payment_status(self):
        try:
            bid_input = input("Booking ID to update payment: ").strip()
            if not bid_input.isdigit():
                print("Invalid Booking ID.")
                return
            bid = int(bid_input)

            print("Set payment: 1. Paid  2. Unpaid")
            choice = input("Choose: ")
            status = 'Paid' if choice == '1' else 'Unpaid'

            cur = self.conn.cursor()
            cur.execute("UPDATE booking SET payment_status = %s WHERE booking_id = %s", (status, bid))
            self.conn.commit()
            print("Payment status updated.")
        except Exception as e:
            print(f"Failed: {e}")

class User:
    def __init__(self, conn, userid, username):
        self.conn = conn
        self.userid = userid
        self.username = username

    def view_available_rooms(self):
        cur = self.conn.cursor()
        today = datetime.today().date()
        cur.execute("""
            SELECT room_no, room_type, room_price FROM room
            WHERE is_avail = TRUE
            AND room_no NOT IN (
                SELECT room_no FROM booking
                WHERE check_in_date <= %s AND check_out_date >= %s
            )
        """, (today, today))
        rooms = cur.fetchall()
        if rooms:
            print("\n--- Available Rooms ---")
            for r in rooms:
                print(f"Room No: {r[0]}, Type: {r[1]}, Price/day: ₹{r[2]}")
        else:
            print("No rooms available.")

    def book_room(self):
        self.view_available_rooms()
        try:
            room_no = int(input("Enter Room No to book: "))
            check_in_str = input("Check-in Date (YYYY-MM-DD) [default today]: ").strip()
            check_in = datetime.strptime(check_in_str, "%Y-%m-%d").date() if check_in_str else datetime.today().date()
            days = int(input("Number of days to stay: "))
            check_out = check_in + timedelta(days=days)

            cur = self.conn.cursor()
            result = ''
            cur.callproc("book_room", [self.userid, room_no, check_in, result])
            self.conn.commit()
            booking_id = cur.lastrowid

            print(f"\nRoom booked from {check_in} to {check_out}. Amount will be calculated at checkout.")
        except Exception as e:
            print(f"Booking failed: {e}")



    def cancel_booking(self):
        cur = self.conn.cursor()
        cur.execute("""
                    SELECT booking_id, room_no, check_in_date
                    FROM booking
                    WHERE userid = %s
                      AND check_out_date IS NULL
                    """, (self.userid,))
        bookings = cur.fetchall()
        if not bookings:
            print("No active bookings.")
            return

        print("\nYour Active Bookings:")
        for b in bookings:
            print(f"ID: {b[0]}, Room: {b[1]}, Check-in: {b[2]}")
        bid = int(input("Booking ID to cancel: "))

        # Get the room number before deleting
        cur.execute("SELECT room_no FROM booking WHERE booking_id = %s AND userid = %s", (bid, self.userid))
        row = cur.fetchone()
        if not row:
            print("Invalid booking ID.")
            return
        room_no = row[0]

        # Delete booking and update room availability
        cur.execute("DELETE FROM booking WHERE booking_id=%s AND userid=%s", (bid, self.userid))
        cur.execute("UPDATE room SET is_avail = TRUE WHERE room_no = %s", (room_no,))
        self.conn.commit()
        print("Booking canceled and room is now available.")

    def view_my_bookings(self):
        cur = self.conn.cursor()
        cur.execute("SELECT booking_id, room_no, check_in_date, check_out_date, amount, payment_status FROM booking WHERE userid=%s ORDER BY booking_date DESC", (self.userid,))
        bookings = cur.fetchall()
        if bookings:
            print("\n--- Your Bookings ---")
            for b in bookings:
                print(f"ID: {b[0]}, Room: {b[1]}, In: {b[2]}, Out: {b[3]}, Amount: ₹{b[4] or 0}, Status: {b[5]}")
        else:
            print("No bookings found.")


    def checkout(self):
        cur = self.conn.cursor()
        cur.execute("""
                    SELECT booking_id, room_no, check_in_date
                    FROM booking
                    WHERE userid = %s
                      AND check_out_date IS NULL
                    """, (self.userid,))
        bookings = cur.fetchall()
        if not bookings:
            print("No active bookings.")
            return

        print("\nYour Active Bookings:")
        for b in bookings:
            print(f"ID: {b[0]}, Room: {b[1]}, Check-in: {b[2]}")
        bid = int(input("Booking ID to checkout: "))
        checkout_date = input("Check-out Date (YYYY-MM-DD): ")
        checkout_date_obj = datetime.strptime(checkout_date, "%Y-%m-%d").date()
        print("Mark payment: 1. Paid  2. Unpaid")
        choice = input("Choose: ")
        status = 'Paid' if choice == '1' else 'Unpaid'

        # Call stored procedure and retrieve output
        args = [bid, checkout_date_obj, status, '']
        result_args = cur.callproc("checkout_guest", args)

        self.conn.commit()
        print(result_args[3])  # OUT parameter (result message)


# Authentication

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def is_strong_password(password):
    return (
        len(password) >= 8 and
        any(c.isdigit() for c in password) and
        any(c.isupper() for c in password) and
        any(c.islower() for c in password)
    )

def is_valid_contact(contact):
    return contact.isdigit() and len(contact) == 10 and contact[0] in '6789'

def admin_login(connconn):
    uname = input("Admin name: ").strip()
    pwd = input("Password: ").strip()
    cur = conn.cursor()
    cur.execute("SELECT adminid, adminname FROM admin WHERE adminname=%s AND password=%s", (uname, pwd))
    row = cur.fetchone()
    if row:
        print(f"\nWelcome Admin {row[1]}!")
        return Admin(conn, row[0], row[1])
    else:
        print("Invalid credentials.")
        return None

def user_register(conn):
    print("\n--- Register New User ---")
    try:
        uname = input("Username: ").strip()

        while True:
            email=input("Email: ").strip()
            if is_valid_email(email):
                break
            print("Invalid email format. Try again.")

        while True:
            pwd = input("Password: ").strip()
            if not is_strong_password(pwd):
                print("Password must be at least 8 characters long and include uppercase, lowercase, and a number.")
                continue

            repeat_pwd = input("Repeat Password: ").strip()
            if pwd != repeat_pwd:
                print("Passwords do not match. Try again.")
                continue

            break

        cur = conn.cursor()
        cur.execute("SELECT * FROM user WHERE email = %s", (email,))
        if cur.fetchone():
            print("Email already registered.")
            exit()
        gender = input("Gender (M/F): ").strip().upper()


        while True:
            dob = input("DOB (YYYY-MM-DD): ").strip()
            try:
                valid_date = datetime.strptime(dob, "%Y-%m-%d")
                if valid_date >= datetime.now():
                    print("Date of birth must be in the past. Please try again.")
                else:
                    break
            except ValueError:
                print("Invalid date format or non-existent date. Please use YYYY-MM-DD.")

        while True:
            contact = input("Contact (10-digit mobile number): ").strip()
            if is_valid_contact(contact):
                break
            print("Invalid contact number. It must be 10 digits and start with 6, 7, 8, or 9.")

        cur.execute("""
            INSERT INTO user(username, email, password, gender, dob, contact)
            VALUES(%s, %s, %s, %s, %s, %s)
        """, (uname, email, pwd, gender, dob, contact))
        conn.commit()
        print("Registration successful!")
    except mysql.connector.IntegrityError as e:
        print("Email already exists.")




# def user_register(conn):
#     print("\n--- Register New User ---")
#     try:
#         uname = input("Username: ").strip()
#         email = input("Email: ").strip()
#         pwd = input("Password: ").strip()
#         gender = input("Gender (M/F): ").strip().upper()
#         dob = input("DOB (YYYY-MM-DD): ").strip()
#         contact = input("Contact: ").strip()
#         cur = conn.cursor()
#         cur.execute("""
#             INSERT INTO user(username, email, password, gender, dob, contact)
#             VALUES(%s, %s, %s, %s, %s, %s)
#         """, (uname, email, pwd, gender, dob, contact))
#         conn.commit()
#         print("Registration successful!")
#     except mysql.connector.IntegrityError as e:
#         print("Email already exists.")


def user_login(conn):
    while True:
        email = input("Email: ").strip()
        if is_valid_email(email):
            break
        print("Invalid email format. Try again.")
    pwd = input("Password: ").strip()
    cur = conn.cursor()
    cur.execute("SELECT userid, username FROM user WHERE email=%s AND password=%s", (email, pwd))
    row = cur.fetchone()
    if row:
        print(f"\nWelcome {row[1]}!")
        return User(conn, row[0], row[1])
    else:
        print("Invalid login.")
        return None

# def user_login(conn):
#     email = input("Email: ").strip()
#     pwd = input("Password: ").strip()
#     cur = conn.cursor()
#     cur.execute("SELECT userid, username FROM user WHERE email=%s AND password=%s", (email, pwd))
#     row = cur.fetchone()
#     if row:
#         print(f"\nWelcome {row[1]}!")
#         return User(conn, row[0], row[1])
#     else:
#         print("Invalid login.")
#         return None



# Menus
def main_menu(conn):
    while True:
        print("\n=== HOTEL BOOKING SYSTEM ===")
        print("1. Admin Login")
        print("2. User Login")
        print("3. Register New User")
        print("4. Exit")
        choice = input("Choose: ")
        if choice == '1':
            admin = admin_login(conn)
            if admin:
                admin_menu(admin)
        elif choice == '2':
            user = user_login(conn)
            if user:
                user_menu(user)
        elif choice == '3':
            user_register(conn)
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid option.")

def admin_menu(admin):
    while True:
        print("\n--- Admin Menu ---")
        print("1. View All Bookings")
        print("2. Add Room")
        print("3. Update Payment Status")
        print("0. Logout")
        ch = input("Choose: ")
        if ch == '1':
            admin.view_all_bookings()
        elif ch == '2':
            admin.add_room()
        elif ch == '3':
            admin.update_payment_status()
        elif ch == '0':
            break
        else:
            print("Invalid choice.")

def user_menu(user):
    while True:
        print("\n--- User Menu ---")
        print("1. View Available Rooms")
        print("2. Book Room")
        print("3. Cancel Booking")
        print("4. View My Bookings")
        print("5. Checkout")
        print("0. Logout")
        ch = input("Choose: ")
        if ch == '1':
            user.view_available_rooms()
        elif ch == '2':
            user.book_room()
        elif ch == '3':
            user.cancel_booking()
        elif ch == '4':
            user.view_my_bookings()
        elif ch == '5':
            user.checkout()
        elif ch == '0':
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    db = DBConnection()
    conn = db.connect()
    main_menu(conn)
