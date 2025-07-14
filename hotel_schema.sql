-- hotel_schema.sql

DROP DATABASE IF EXISTS python_project;
CREATE DATABASE python_project;
USE python_project;

-- Tables
CREATE TABLE user (
  userid INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(25),
  email VARCHAR(50) UNIQUE,
  password VARCHAR(50) NOT NULL,
  gender VARCHAR(1),
  dob DATE,
  contact VARCHAR(15)
);

CREATE TABLE room (
  room_no INT PRIMARY KEY AUTO_INCREMENT,
  room_type VARCHAR(20),
  room_price INT,
  is_avail BOOLEAN DEFAULT TRUE
);

CREATE TABLE booking (
  booking_id INT PRIMARY KEY AUTO_INCREMENT,
  check_in_date DATE,
  check_out_date DATE,
  userid INT,
  room_no INT,
  amount INT,
  payment_status ENUM('Paid', 'Unpaid') DEFAULT 'Unpaid',
  booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (userid) REFERENCES user(userid),
  FOREIGN KEY (room_no) REFERENCES room(room_no)
);

CREATE TABLE admin (
  adminid INT PRIMARY KEY AUTO_INCREMENT,
  adminname VARCHAR(25),
  password VARCHAR(50) NOT NULL
);

-- Sample Data
INSERT INTO user (username, email, gender, dob, contact, password) VALUES
('Ankit', 'ankit@example.com', 'M', '1995-06-15', '9876543210', 'ankit123'),
('Priya', 'priya@example.com', 'F', '1998-03-22', '9876543211', 'priya123');

INSERT INTO room (room_type, room_price) VALUES
('Standard', 1800), ('Deluxe', 3000), ('Luxury', 4500);

INSERT INTO admin (adminname, password) VALUES ('admin1', 'adminpass1');

-- Triggers
DELIMITER $$
CREATE TRIGGER after_booking_insert
AFTER INSERT ON booking
FOR EACH ROW
BEGIN
    IF NEW.check_out_date IS NULL THEN
        UPDATE room SET is_avail = FALSE WHERE room_no = NEW.room_no;
    END IF;
END$$
DELIMITER ;

-- Stored Procedures
DELIMITER $$
CREATE PROCEDURE book_room(
    IN p_userid INT,
    IN p_room_no INT,
    IN p_check_in_date DATE,
    OUT result VARCHAR(100)
)
BEGIN
    DECLARE v_is_avail BOOLEAN;
    SELECT is_avail INTO v_is_avail FROM room WHERE room_no = p_room_no;
    IF v_is_avail THEN
        INSERT INTO booking (check_in_date, userid, room_no)
        VALUES (p_check_in_date, p_userid, p_room_no);
        UPDATE room SET is_avail = FALSE WHERE room_no = p_room_no;
        SET result = 'Room booked successfully.';
    ELSE
        SET result = 'Room not available.';
    END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE checkout_guest(
    IN p_booking_id INT,
    IN p_check_out_date DATE,
    IN p_payment_status VARCHAR(10),
    OUT result VARCHAR(100)
)
BEGIN
    DECLARE v_check_in DATE;
    DECLARE v_room_price INT;
    DECLARE v_days INT;
    DECLARE v_amount INT;
    DECLARE v_room_no INT;

    SELECT b.check_in_date, r.room_price, b.room_no INTO v_check_in, v_room_price, v_room_no
    FROM booking b JOIN room r ON b.room_no = r.room_no
    WHERE b.booking_id = p_booking_id;

    IF v_check_in IS NOT NULL THEN
        SET v_days = DATEDIFF(p_check_out_date, v_check_in);
        SET v_amount = v_days * v_room_price;

        START TRANSACTION;
        UPDATE booking
        SET check_out_date = p_check_out_date, amount = v_amount, payment_status = p_payment_status
        WHERE booking_id = p_booking_id;

        UPDATE room SET is_avail = TRUE WHERE room_no = v_room_no;
        COMMIT;

        SET result = CONCAT('Checkout successful. Total: ₹', v_amount, ', Status: ', p_payment_status);
        -- add room to availability after successfull payment and checkout or cancel booking
    ELSE
        SET result = 'Booking ID not found.';
    END IF;
END$$
DELIMITER ;