-- CORE RULE (one function holds all the logic)
--   Client role      → MUST have client_profiles row, MUST NOT have staff_profiles
--   Any other role   → MUST have staff_profiles row,  MUST NOT have client_profiles
CREATE OR REPLACE FUNCTION assert_user_profile(p_user_id uuid)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    v_role_name  text;
    v_has_client boolean;
    v_has_staff  boolean;
BEGIN
    SELECT lower(r.role_name)
      INTO v_role_name
      FROM users u
      JOIN roles r ON r.role_id = u.role_id
     WHERE u.user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN;        -- user no longer exists (e.g. deleted in same txn): nothing to check
    END IF;

    v_has_client := EXISTS (SELECT 1 FROM client_profiles WHERE user_id = p_user_id);
    v_has_staff  := EXISTS (SELECT 1 FROM staff_profiles  WHERE user_id = p_user_id);

    IF v_role_name = 'client' THEN
        IF NOT v_has_client THEN
            RAISE EXCEPTION 'Client user % must have a client_profiles row', p_user_id
                USING ERRCODE = 'integrity_constraint_violation';
        END IF;
        IF v_has_staff THEN
            RAISE EXCEPTION 'Client user % must not have a staff_profiles row', p_user_id
                USING ERRCODE = 'integrity_constraint_violation';
        END IF;
    ELSE   -- Field Agent, Data Entry Staff, Secretary, Director, and the 6th role
        IF NOT v_has_staff THEN
            RAISE EXCEPTION 'Staff user % (role: %) must have a staff_profiles row',
                            p_user_id, v_role_name
                USING ERRCODE = 'integrity_constraint_violation';
        END IF;
        IF v_has_client THEN
            RAISE EXCEPTION 'Staff user % must not have a client_profiles row', p_user_id
                USING ERRCODE = 'integrity_constraint_violation';
        END IF;
    END IF;
END;
$$;

-- TRIGGER WRAPPER (shared by users, client_profiles, staff_profiles)
-- All three tables have a user_id column, so one function serves all.
CREATE OR REPLACE FUNCTION trg_enforce_profile_rules()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM assert_user_profile(OLD.user_id);     -- NEW doesn't exist on DELETE
    ELSE
        PERFORM assert_user_profile(NEW.user_id);
        IF TG_OP = 'UPDATE' AND OLD.user_id IS DISTINCT FROM NEW.user_id THEN
            PERFORM assert_user_profile(OLD.user_id); -- profile re-pointed to another user
        END IF;
    END IF;
    RETURN NULL;   -- return value is ignored for AFTER triggers
END;
$$;

-- THE THREE DEFERRED CONSTRAINT TRIGGERS
-- Fires on a new user or a role change
DROP TRIGGER IF EXISTS trg_users_require_profile ON users;
CREATE CONSTRAINT TRIGGER trg_users_require_profile
    AFTER INSERT OR UPDATE OF role_id ON users
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW
    EXECUTE FUNCTION trg_enforce_profile_rules();

-- Fires when a client profile is added, changed or removed
DROP TRIGGER IF EXISTS trg_client_profiles_rules ON client_profiles;
CREATE CONSTRAINT TRIGGER trg_client_profiles_rules
    AFTER INSERT OR UPDATE OR DELETE ON client_profiles
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW
    EXECUTE FUNCTION trg_enforce_profile_rules();

-- Fires when a staff profile is added, changed or removed
DROP TRIGGER IF EXISTS trg_staff_profiles_rules ON staff_profiles;
CREATE CONSTRAINT TRIGGER trg_staff_profiles_rules
    AFTER INSERT OR UPDATE OR DELETE ON staff_profiles
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW
    EXECUTE FUNCTION trg_enforce_profile_rules();