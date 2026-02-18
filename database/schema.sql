-- Validation Rules
-- Username: 3-20 characters, letters, numbers, and underscores only
-- Email: Valid email format required
-- Password: Minimum 8 characters, must include uppercase, lowercase, number, and special character
-- Names: At least 2 characters, letters only
-- Phone: Optional, must be at least 10 digits
-- Bio: Optional, maximum 500 characters

-- Users Table with validation constraints
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    bio VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Constraints for validation rules
    CONSTRAINT username_length CHECK (CHAR_LENGTH(username) BETWEEN 3 AND 20),
    CONSTRAINT username_format CHECK (username REGEXP '^[a-zA-Z0-9_]+$'),
    CONSTRAINT email_format CHECK (email REGEXP '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'),
    CONSTRAINT password_length CHECK (CHAR_LENGTH(password) >= 8),
    CONSTRAINT first_name_length CHECK (CHAR_LENGTH(first_name) >= 2),
    CONSTRAINT first_name_format CHECK (first_name REGEXP '^[a-zA-Z]+$'),
    CONSTRAINT last_name_length CHECK (CHAR_LENGTH(last_name) >= 2),
    CONSTRAINT last_name_format CHECK (last_name REGEXP '^[a-zA-Z]+$'),
    CONSTRAINT phone_length CHECK (phone IS NULL OR CHAR_LENGTH(REPLACE(phone, '+', '')) >= 10),
    CONSTRAINT bio_length CHECK (bio IS NULL OR CHAR_LENGTH(bio) <= 500)
);

-- Create index for faster email lookups
CREATE INDEX idx_email ON users(email);

-- Create index for faster username lookups
CREATE INDEX idx_username ON users(username);

