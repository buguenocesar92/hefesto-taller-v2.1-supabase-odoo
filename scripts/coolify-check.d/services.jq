def problems($name; $s):
  [
    (if ($s.ports // []) | length > 0 then "ports" else empty end),
    (if ($s.container_name // null) != null then "container_name fijo" else empty end),
    (if ($s.privileged // false) == true then "privileged" else empty end),
    (if ($s.cap_add // []) | length > 0 then "cap_add" else empty end),
    (if ($s.devices // []) | length > 0 then "devices" else empty end),
    (if ($s.network_mode // null) == "host" then "network_mode: host" else empty end),
    (if ($s.pid // null) == "host" then "pid: host" else empty end),
    (if ($s.ipc // null) == "host" then "ipc: host" else empty end),
    (if ($s.security_opt // []) | any(. | test("unconfined")) then "security_opt unconfined" else empty end),
    (if ($s.volumes // []) | any(. | type == "object" and ((.source // "") | test("docker.sock"))) then "bind a docker.sock" else empty end)
  ];

.services // {}
| to_entries[]
| select((.value.profiles // []) | length == 0)
| . as $entry
| ([$entry.key] + problems($entry.key; $entry.value)) as $list
| $list[0] as $name
| ($list[1:] | join(", ")) as $joined
| if $joined != "" then "\($name): \($joined)" else empty end
