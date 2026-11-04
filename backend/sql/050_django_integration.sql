-- Install ONCE (safe to re-run) in the existing project database as its trusted owner.
-- Requires the previously installed roles, views, and staff routines. No seed/password resets.
BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;

CREATE OR REPLACE FUNCTION public.app_authenticate(p_phone text, p_password text)
RETURNS TABLE(user_id uuid, full_name text, role_name text)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE person record; stored text; matches boolean;
BEGIN
    IF p_phone IS NULL OR p_password IS NULL OR length(p_phone)>20
       OR octet_length(p_password)>72 OR p_password='' THEN RETURN; END IF;
    SELECT u.user_id,u.full_name,u.password_hash,u.is_active,r.role_name
    INTO person FROM public.users u JOIN public.roles r ON r.role_id=u.role_id
    WHERE u.phone=p_phone;
    stored := COALESCE(person.password_hash, '$2a$10$fMn/Zfqq88Ai2E1hJLfhe.rV8Dp4AA0H8xvx5r8NdSs4GhKZpzUEO');
    IF stored !~ '^\$2[aby]\$[0-9]{2}\$' THEN RETURN; END IF;
    -- pgcrypto recognizes 2a salts. Modern Python bcrypt emits 2b; for the
    -- enforced <=72-byte inputs the compatible calculation uses the 2a tag.
    -- Normalize only the comparison value, never the stored password hash.
    stored := '$2a' || substr(stored,4);
    matches := public.crypt(p_password,stored)=stored;
    IF person.user_id IS NOT NULL AND person.is_active AND matches
       AND person.role_name IN ('Client','Field Agent','Data Entry Staff','Secretary','Director') THEN
        RETURN QUERY SELECT person.user_id,person.full_name::text,person.role_name::text;
    END IF;
END $$;
REVOKE ALL ON FUNCTION public.app_authenticate(text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.app_authenticate(text,text) TO alsj_app_login;

-- Called only by the trusted server, using the identity held in its private session.
CREATE OR REPLACE FUNCTION public.app_session_identity(p_user uuid)
RETURNS TABLE(user_id uuid,full_name text,role_name text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
SELECT u.user_id,u.full_name::text,r.role_name::text
FROM public.users u JOIN public.roles r ON r.role_id=u.role_id
WHERE u.user_id=p_user AND u.is_active
  AND r.role_name IN ('Client','Field Agent','Data Entry Staff','Secretary','Director')
$$;
REVOKE ALL ON FUNCTION public.app_session_identity(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.app_session_identity(uuid) TO alsj_app_login;

CREATE OR REPLACE FUNCTION public.field_agent_change_stage(p_application_id uuid,p_stage_id integer)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE actor uuid := NULLIF(current_setting('app.current_user_id',true),'')::uuid;
BEGIN
    PERFORM 1 FROM public.users u JOIN public.roles r ON r.role_id=u.role_id
    WHERE u.user_id=actor AND u.is_active AND r.role_name='Field Agent' FOR SHARE OF u,r;
    IF NOT FOUND THEN RAISE EXCEPTION 'Active Field Agent identity required' USING ERRCODE='42501'; END IF;
    PERFORM 1 FROM public.applications WHERE application_id=p_application_id AND assigned_agent_id=actor FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Application is not assigned to this Field Agent' USING ERRCODE='42501'; END IF;
    PERFORM public.change_stage(p_application_id,p_stage_id,actor);
END $$;
REVOKE ALL ON FUNCTION public.field_agent_change_stage(uuid,integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.field_agent_change_stage(uuid,integer) TO alsj_field_agent;

CREATE OR REPLACE FUNCTION public.secretary_appointment_choices()
RETURNS TABLE(user_id uuid,full_name text,kind text)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE actor uuid := NULLIF(current_setting('app.current_user_id',true),'')::uuid;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.users u JOIN public.roles r ON r.role_id=u.role_id
        WHERE u.user_id=actor AND u.is_active AND r.role_name='Secretary') THEN
        RAISE EXCEPTION 'Secretary identity required' USING ERRCODE='42501';
    END IF;
    RETURN QUERY
    SELECT u.user_id,u.full_name::text,'client'::text FROM public.users u
    JOIN public.client_profiles c ON c.user_id=u.user_id WHERE u.is_active
    UNION ALL
    SELECT u.user_id,u.full_name::text,'staff'::text FROM public.users u
    JOIN public.staff_profiles s ON s.user_id=u.user_id WHERE u.is_active;
END $$;
REVOKE ALL ON FUNCTION public.secretary_appointment_choices() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.secretary_appointment_choices() TO alsj_secretary;

-- Only safe profile reads needed by the existing Director dashboard and tables.
GRANT SELECT ON public.client_profiles,public.staff_profiles TO alsj_director;
DROP POLICY IF EXISTS django_director_profiles ON public.client_profiles;
CREATE POLICY django_director_profiles ON public.client_profiles FOR SELECT TO alsj_director USING(true);
DROP POLICY IF EXISTS django_director_staff ON public.staff_profiles;
CREATE POLICY django_director_staff ON public.staff_profiles FOR SELECT TO alsj_director USING(true);
GRANT SELECT ON public.stage_history TO alsj_field_agent;
ALTER TABLE public.stage_history ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS field_agent_history ON public.stage_history;
CREATE POLICY field_agent_history ON public.stage_history FOR SELECT TO alsj_field_agent
USING(application_id IN (SELECT application_id FROM public.applications));
-- Other roles already have their own history SELECT policies.
COMMIT;
