-- register_client: creates users + client_profiles atomically, returns the new user_id
CREATE OR REPLACE FUNCTION register_client(
    p_full_name     varchar,
    p_phone         varchar,
    p_password_hash varchar,            -- bcrypt hash computed by the app, NEVER plaintext
    p_national_id   varchar,
    p_email         varchar DEFAULT NULL,
    p_dob           date    DEFAULT NULL,
    p_address       varchar DEFAULT NULL,
    p_language      varchar DEFAULT 'EN'
)
RETURNS uuid
LANGUAGE plpgsql
AS $$
DECLARE
    v_role_id smallint;
    v_user_id uuid;
BEGIN
    SELECT role_id INTO v_role_id FROM roles WHERE lower(role_name) = 'client';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Role "Client" is not seeded in roles';
    END IF;

    INSERT INTO users (full_name, email, phone, password_hash, role_id)
    VALUES (p_full_name, p_email, p_phone, p_password_hash, v_role_id)
    RETURNING user_id INTO v_user_id;

    INSERT INTO client_profiles (user_id, national_id, date_of_birth, address, preferred_language)
    VALUES (v_user_id, p_national_id, p_dob, p_address, p_language);

    RETURN v_user_id;
END;
$$;

-- register_staff: creates users + staff_profiles atomically
CREATE OR REPLACE FUNCTION register_staff(
    p_full_name     varchar,
    p_phone         varchar,
    p_password_hash varchar,
    p_role_name     varchar,            -- 'Field Agent', 'Secretary', ...
    p_employee_no   varchar,
    p_email         varchar DEFAULT NULL,
    p_date_hired    date    DEFAULT CURRENT_DATE
)
RETURNS uuid
LANGUAGE plpgsql
AS $$
DECLARE
    v_role_id smallint;
    v_user_id uuid;
BEGIN
    IF lower(p_role_name) = 'client' THEN
        RAISE EXCEPTION 'Use register_client() for Client users';
    END IF;

    SELECT role_id INTO v_role_id FROM roles WHERE lower(role_name) = lower(p_role_name);
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown role: %', p_role_name;
    END IF;

    INSERT INTO users (full_name, email, phone, password_hash, role_id)
    VALUES (p_full_name, p_email, p_phone, p_password_hash, v_role_id)
    RETURNING user_id INTO v_user_id;

    INSERT INTO staff_profiles (user_id, employee_no, date_hired)
    VALUES (v_user_id, p_employee_no, p_date_hired);

    RETURN v_user_id;
END;
$$;