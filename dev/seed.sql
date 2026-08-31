-- Тестовые данные для локальной разработки (docker compose).
USE opensips;

INSERT INTO dispatcher (setid, destination, socket, state, probe_mode, weight, priority, attrs, description) VALUES
  (200, 'sip:10.10.10.11:5060', NULL, 0, 2, '1', 10, NULL, 'Видеосервер A'),
  (200, 'sip:10.10.10.12:5060', NULL, 0, 2, '1', 5,  NULL, 'Видеосервер A (резерв)'),
  (201, 'sip:10.10.20.11:5060', NULL, 0, 2, '1', 10, NULL, 'Видеосервер B'),
  (300, 'sip:10.10.30.11:5060', NULL, 0, 2, '1', 10, NULL, 'Аудио-шлюз');

INSERT INTO load_balancer (group_id, dst_uri, resources, probe_mode, attrs, description) VALUES
  (1, 'sip:10.20.10.11:5060', 'pstn=100;transc=25', 2, NULL, 'Транскодер 1'),
  (1, 'sip:10.20.10.12:5060', 'pstn=100;transc=25', 2, NULL, 'Транскодер 2');

-- SIP-регистрации (usrloc db_mode 2/3). expires - абсолютный unix-time, 0 - постоянный контакт.
INSERT INTO location
  (username, domain, contact, received, path, expires, q, callid, cseq, last_modified, flags, cflags, user_agent, socket, methods, sip_instance, attr) VALUES
  ('1234201', 'voip.local', 'sip:1234201@10.30.1.21:5060', 'sip:10.30.1.21:5060', NULL, UNIX_TIMESTAMP() + 1800, 1.0, 'a1b2c3-node-01', 14, NOW(), 0, NULL, 'Polycom Trio 8800/6.2.0', 'udp:10.10.10.11:5060', 8063, NULL, NULL),
  ('1234205', 'voip.local', 'sip:1234205@10.30.1.35:5060', 'sip:10.30.1.35:5060', NULL, UNIX_TIMESTAMP() + 900,  1.0, 'd4e5f6-node-02', 7,  NOW(), 0, NULL, 'Yealink VP59 91.15.0.16', 'udp:10.10.10.11:5060', 8063, NULL, NULL),
  ('1234202', 'voip.local', 'sip:1234202@10.30.2.14:5060', 'sip:10.30.2.14:5060', NULL, UNIX_TIMESTAMP() - 120,  1.0, 'g7h8i9-node-03', 3,  NOW(), 0, NULL, 'Grandstream GXP2170 1.0.11', 'udp:10.10.20.11:5060', 8063, NULL, NULL),
  ('1234301', 'voip.local', 'sip:1234301@10.30.3.9:5060',  'sip:10.30.3.9:5060',  NULL, 0,                       1.0, 'j1k2l3-gw-01',  1,  NOW(), 0, NULL, 'OpenSIPS gateway', 'udp:10.10.30.11:5060', 8063, NULL, 'permanent');

-- Dialplan: dpid 1 - нормализация в E.164, dpid 2 - короткие номера.
INSERT INTO dialplan (dpid, pr, match_op, match_exp, match_flags, subst_exp, repl_exp, timerec, disabled, attrs) VALUES
  (1, 10, 1, '^8[0-9]{10}$',  0, '^8([0-9]{10})$', '7\\1',    NULL, 0, 'e164'),
  (1, 20, 1, '^\\+7[0-9]{10}$', 0, '^\\+7([0-9]{10})$', '7\\1', NULL, 0, 'e164'),
  (1, 30, 0, '1234',          0, NULL,             '1234201', NULL, 0, 'short'),
  (2, 10, 1, '^12([0-9]{5})$', 0, NULL,            NULL,      NULL, 1, 'reserved');

-- RTPEngine: два медиасервера в наборе 0.
INSERT INTO rtpengine (socket, set_id) VALUES
  ('udp:10.40.0.11:2223', 0),
  ('udp:10.40.0.12:2223', 0);

-- Списки номеров: запреты и одно разрешающее правило поверх запрета.
INSERT INTO userblacklist (username, domain, prefix, whitelist) VALUES
  ('1234201', 'voip.local', '810', 0),
  ('1234201', 'voip.local', '81049', 1),
  ('1234205', 'voip.local', '900',  0);

INSERT INTO globalblacklist (prefix, whitelist, description) VALUES
  ('80900', 0, 'Платные номера'),
  ('8809',  0, 'Платные номера'),
  ('112',   1, 'Экстренные службы');

-- Доверенные адреса (permissions): узел и подсеть.
INSERT INTO address (grp, ip, mask, port, proto, pattern, context_info) VALUES
  (1, '10.10.10.11', 32, 5060, 'udp', NULL, 'video-a'),
  (1, '10.10.20.11', 32, 5060, 'udp', NULL, 'video-b'),
  (2, '10.30.0.0',   16, 0,    'any', NULL, 'абонентская сеть');
