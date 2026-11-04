-- =========================================================================
-- Description: audit_logs joined with the name and role of the acting user 
--              (displays "system" when user_id is null), newest first.
-- =========================================================================

CREATE OR REPLACE VIEW v_audit_trail AS
SELECT 
    al.log_id,
    COALESCE(u.full_name, 'system') AS actor_name,
    COALESCE(r.role_name, 'system') AS actor_role,
    al.action,
    al.entity_type,
    al.entity_id,
    al.ip_address,
    al.created_at
FROM audit_logs al
LEFT JOIN users u ON al.user_id = u.user_id
LEFT JOIN roles r ON u.role_id = r.role_id
ORDER BY al.created_at DESC;