---
type: regex
target: last_message
pattern: '(app|router)\.(post|get|put|delete)\(|create table|import .* from |export (default |async )?function|```(ts|typescript|js|javascript|sql)'
match: not_contains
flags: i
---
