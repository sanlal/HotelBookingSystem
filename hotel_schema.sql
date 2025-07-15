DROP DATABASE IF EXISTS checkKarthe;
CREATE DATABASE checkKarthe;
USE checkKarthe;

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
CREATE TRIGGER after_booking_delete
AFTER DELETE ON booking
FOR EACH ROW
BEGIN
    UPDATE room SET is_avail = TRUE WHERE room_no = OLD.room_no;
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

CREATE PROCEDURE checkout_guest (
    IN p_booking_id INT,
    IN p_checkout_date DATE,
    IN p_payment_status VARCHAR(10),
    OUT result VARCHAR(255)
)
proc: BEGIN
    DECLARE v_checkin_date DATE;
    DECLARE v_room_no INT;
    DECLARE v_days INT;
    DECLARE v_price_per_day INT;
    DECLARE v_amount INT;
    DECLARE v_exists INT;
    DECLARE v_out DATE;

    -- check if booking exists
    SELECT COUNT(*) INTO v_exists FROM booking WHERE booking_id = p_booking_id;
    IF v_exists = 0 THEN
        SET result = '❌ Booking ID does not exist.';
        LEAVE proc;
    END IF;

    -- check if already checked out
    SELECT check_out_date INTO v_out FROM booking WHERE booking_id = p_booking_id;
    IF v_out IS NOT NULL THEN
        SET result = '⚠️ Booking already completed.';
        LEAVE proc;
    END IF;

    -- validate checkout date is today or future
    IF p_checkout_date < CURDATE() THEN
        SET result = '⛔ Checkout date must be today or in the future.';
        LEAVE proc;
    END IF;

    -- get check-in and room info
    SELECT check_in_date, room_no INTO v_checkin_date, v_room_no
    FROM booking WHERE booking_id = p_booking_id;

    -- calculate duration
    SET v_days = DATEDIFF(p_checkout_date, v_checkin_date);
    IF v_days <= 0 THEN
        SET result = '❌ Invalid checkout date. Must be after check-in.';
        LEAVE proc;
    END IF;

    -- calculate payment
    SELECT room_price INTO v_price_per_day FROM room WHERE room_no = v_room_no;
    SET v_amount = v_days * v_price_per_day;

    -- update booking info
    UPDATE booking
    SET check_out_date = p_checkout_date,
        amount = v_amount,
        payment_status = p_payment_status
    WHERE booking_id = p_booking_id;

    -- mark room as available
    UPDATE room SET is_avail = TRUE WHERE room_no = v_room_no;

    -- final result message
    SET result = CONCAT('✅ Checkout successful. Total: ₹', v_amount, ', Status: ', p_payment_status);
END$$

DELIMITER ;

DROP PROCEDURE IF EXISTS checkout_guest;



DROP PROCEDURE IF EXISTS checkout_guest;
DELIMITER $$

CREATE PROCEDURE checkout_guest (
    IN p_booking_id INT,
    IN p_checkout_date DATE,
    IN p_payment_status VARCHAR(10),
    OUT result VARCHAR(255)
)
proc: BEGIN
    DECLARE v_checkin_date DATE;
    DECLARE v_room_no INT;
    DECLARE v_days INT;
    DECLARE v_price_per_day INT;
    DECLARE v_amount INT;
    DECLARE v_exists INT;
    DECLARE v_out DATE;

    SELECT COUNT(*) INTO v_exists FROM booking WHERE booking_id = p_booking_id;
    IF v_exists = 0 THEN
        SET result = '❌ Booking ID does not exist.';
        LEAVE proc;
    END IF;

    SELECT check_out_date INTO v_out FROM booking WHERE booking_id = p_booking_id;
    IF v_out IS NOT NULL THEN
        SET result = '⚠️ Booking already completed.';
        LEAVE proc;
    END IF;

    IF p_checkout_date < CURDATE() THEN
        SET result = '⛔ Checkout date must be today or in the future.';
        LEAVE proc;
    END IF;

    SELECT check_in_date, room_no INTO v_checkin_date, v_room_no
    FROM booking WHERE booking_id = p_booking_id;

    SET v_days = DATEDIFF(p_checkout_date, v_checkin_date);
    IF v_days <= 0 THEN
        SET result = '❌ Invalid checkout date. Must be after check-in.';
        LEAVE proc;
    END IF;

    SELECT room_price INTO v_price_per_day FROM room WHERE room_no = v_room_no;
    SET v_amount = v_days * v_price_per_day;

    UPDATE booking
    SET check_out_date = p_checkout_date,
        amount = v_amount,
        payment_status = p_payment_status
    WHERE booking_id = p_booking_id;

    UPDATE room SET is_avail = TRUE WHERE room_no = v_room_no;

    SET result = CONCAT('✅ Checkout successful. Total: ₹', v_amount, ', Status: ', p_payment_status);
END$$
DELIMITER ;


alter table booking add status
enum('Booked', 'Cancelled') default 'Booked';


create INDEX idx_booking_date ON booking(booking_date);


select * from room;
select * from user;
select * from booking;
