CREATE TABLE IF NOT EXISTS version (
    table_name CHAR(32) NOT NULL,
    table_version INT UNSIGNED DEFAULT 0 NOT NULL,
    CONSTRAINT t_name_idx UNIQUE (table_name)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('tcp_mgm','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);

CREATE TABLE IF NOT EXISTS tcp_mgm (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    proto CHAR(8) DEFAULT 'any' NOT NULL,
    remote_addr CHAR(43) DEFAULT NULL,
    remote_port INT UNSIGNED DEFAULT 0 NOT NULL,
    local_addr CHAR(43) DEFAULT NULL,
    local_port INT UNSIGNED DEFAULT 0 NOT NULL,
    priority INT DEFAULT 0 NOT NULL,
    attrs CHAR(255) DEFAULT NULL,
    connect_timeout INT UNSIGNED DEFAULT 100 NOT NULL,
    con_lifetime INT UNSIGNED DEFAULT 120 NOT NULL,
    msg_read_timeout INT UNSIGNED DEFAULT 4 NOT NULL,
    send_threshold INT UNSIGNED DEFAULT 0 NOT NULL,
    no_new_conn INT UNSIGNED DEFAULT 0 NOT NULL,
    alias_mode INT UNSIGNED DEFAULT 0 NOT NULL,
    parallel_read INT UNSIGNED DEFAULT 0 NOT NULL,
    keepalive INT UNSIGNED DEFAULT 1 NOT NULL,
    keepcount INT UNSIGNED DEFAULT 9 NOT NULL,
    keepidle INT UNSIGNED DEFAULT 7200 NOT NULL,
    keepinterval INT UNSIGNED DEFAULT 75 NOT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('address','5') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS address (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    grp SMALLINT(5) UNSIGNED DEFAULT 0 NOT NULL,
    ip CHAR(50) NOT NULL,
    mask TINYINT DEFAULT 32 NOT NULL,
    port SMALLINT(5) UNSIGNED DEFAULT 0 NOT NULL,
    proto CHAR(4) DEFAULT 'any' NOT NULL,
    pattern CHAR(64) DEFAULT NULL,
    context_info CHAR(32) DEFAULT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('b2b_entities','2') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS b2b_entities (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    type INT(2) NOT NULL,
    state INT(2) NOT NULL,
    ruri CHAR(255),
    from_uri CHAR(255) NOT NULL,
    to_uri CHAR(255) NOT NULL,
    from_dname CHAR(64),
    to_dname CHAR(64),
    tag0 CHAR(64) NOT NULL,
    tag1 CHAR(64),
    callid CHAR(128) NOT NULL,
    cseq0 INT(11) NOT NULL,
    cseq1 INT(11),
    contact0 CHAR(255) NOT NULL,
    contact1 CHAR(255),
    route0 TEXT,
    route1 TEXT,
    sockinfo_srv CHAR(64),
    param CHAR(255) NOT NULL,
    mod_name CHAR(32) NOT NULL,
    storage BLOB(4096) DEFAULT NULL,
    lm INT(11) NOT NULL,
    lrc INT(11),
    lic INT(11),
    leg_cseq INT(11),
    leg_route TEXT,
    leg_tag CHAR(64),
    leg_contact CHAR(255),
    leg_sockinfo CHAR(255),
    CONSTRAINT b2b_entities_idx UNIQUE (type, tag0, tag1, callid)
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS b2b_entities_param ON b2b_entities (param);

INSERT INTO version (table_name, table_version) values ('b2b_logic','5') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS b2b_logic (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    si_key CHAR(64) NOT NULL,
    scenario CHAR(64),
    sstate INT(2) NOT NULL,
    lifetime INT(10) DEFAULT 0 NOT NULL,
    e1_type INT(2) NOT NULL,
    e1_sid CHAR(64),
    e1_from CHAR(255) NOT NULL,
    e1_to CHAR(255) NOT NULL,
    e1_key CHAR(64) NOT NULL,
    e1_sdp TEXT,
    e2_type INT(2) NOT NULL,
    e2_sid CHAR(64),
    e2_from CHAR(255) NOT NULL,
    e2_to CHAR(255) NOT NULL,
    e2_key CHAR(64) NOT NULL,
    e2_sdp TEXT,
    e3_type INT(2),
    e3_sid CHAR(64),
    e3_from CHAR(255),
    e3_to CHAR(255),
    e3_key CHAR(64),
    CONSTRAINT b2b_logic_idx UNIQUE (si_key)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('location','1013') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS location (
    contact_id BIGINT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    username CHAR(64) DEFAULT '' NOT NULL,
    domain CHAR(64) DEFAULT NULL,
    contact TEXT NOT NULL,
    received CHAR(255) DEFAULT NULL,
    path CHAR(255) DEFAULT NULL,
    expires INT(10) UNSIGNED NOT NULL,
    q FLOAT(10,2) DEFAULT 1.0 NOT NULL,
    callid CHAR(255) DEFAULT 'Default-Call-ID' NOT NULL,
    cseq INT(11) DEFAULT 13 NOT NULL,
    last_modified DATETIME DEFAULT '1900-01-01 00:00:01' NOT NULL,
    flags INT(11) DEFAULT 0 NOT NULL,
    cflags CHAR(255) DEFAULT NULL,
    user_agent CHAR(255) DEFAULT '' NOT NULL,
    socket CHAR(64) DEFAULT NULL,
    methods INT(11) DEFAULT NULL,
    sip_instance CHAR(255) DEFAULT NULL,
    kv_store TEXT(512) DEFAULT NULL,
    attr CHAR(255) DEFAULT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('dialplan','5') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS dialplan (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    dpid INT(11) NOT NULL,
    pr INT(11) DEFAULT 0 NOT NULL,
    match_op INT(11) NOT NULL,
    match_exp CHAR(64) NOT NULL,
    match_flags INT(11) DEFAULT 0 NOT NULL,
    subst_exp CHAR(64) DEFAULT NULL,
    repl_exp CHAR(32) DEFAULT NULL,
    timerec CHAR(255) DEFAULT NULL,
    disabled INT(11) DEFAULT 0 NOT NULL,
    attrs CHAR(255) DEFAULT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('emergency_routing','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS emergency_routing (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    selectiveRoutingID CHAR(11) NOT NULL,
    routingESN INT(5) UNSIGNED DEFAULT 0 NOT NULL,
    npa INT(3) UNSIGNED DEFAULT 0 NOT NULL,
    esgwri CHAR(50) NOT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('emergency_report','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS emergency_report (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    callid CHAR(25) NOT NULL,
    selectiveRoutingID CHAR(11) NOT NULL,
    routingESN INT(5) UNSIGNED DEFAULT 0 NOT NULL,
    npa INT(3) UNSIGNED DEFAULT 0 NOT NULL,
    esgwri CHAR(50) NOT NULL,
    lro CHAR(20) NOT NULL,
    VPC_organizationName CHAR(50) NOT NULL,
    VPC_hostname CHAR(50) NOT NULL,
    VPC_timestamp CHAR(30) NOT NULL,
    result CHAR(4) NOT NULL,
    disposition CHAR(10) NOT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('emergency_service_provider','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS emergency_service_provider (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    organizationName CHAR(50) NOT NULL,
    hostId CHAR(30) NOT NULL,
    nenaId CHAR(50) NOT NULL,
    contact CHAR(20) NOT NULL,
    certUri CHAR(50) NOT NULL,
    nodeIP CHAR(20) NOT NULL,
    attribution INT(2) UNSIGNED NOT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('domain','4') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS domain (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    domain CHAR(64) DEFAULT '' NOT NULL,
    attrs CHAR(255) DEFAULT NULL,
    accept_subdomain INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    last_modified DATETIME DEFAULT '1900-01-01 00:00:01' NOT NULL,
    CONSTRAINT domain_idx UNIQUE (domain)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('userblacklist','2') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS userblacklist (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    username CHAR(64) DEFAULT '' NOT NULL,
    domain CHAR(64) DEFAULT '' NOT NULL,
    prefix CHAR(64) DEFAULT '' NOT NULL,
    whitelist TINYINT(1) DEFAULT 0 NOT NULL
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS userblacklist_idx ON userblacklist (username, domain, prefix);

INSERT INTO version (table_name, table_version) values ('globalblacklist','2') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS globalblacklist (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    prefix CHAR(64) DEFAULT '' NOT NULL,
    whitelist TINYINT(1) DEFAULT 0 NOT NULL,
    description CHAR(255) DEFAULT NULL
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS globalblacklist_idx ON globalblacklist (prefix);

INSERT INTO version (table_name, table_version) values ('dr_gateways','6') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS dr_gateways (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    gwid CHAR(64) NOT NULL,
    type INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    address CHAR(128) NOT NULL,
    strip INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    pri_prefix CHAR(16) DEFAULT NULL,
    attrs CHAR(255) DEFAULT NULL,
    probe_mode INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    state INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    socket CHAR(128) DEFAULT NULL,
    description CHAR(128) DEFAULT NULL,
    CONSTRAINT dr_gw_idx UNIQUE (gwid)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('dr_rules','4') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS dr_rules (
    ruleid INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    groupid CHAR(255) NOT NULL,
    prefix CHAR(64) NOT NULL,
    timerec CHAR(255) DEFAULT NULL,
    priority INT(11) DEFAULT 0 NOT NULL,
    routeid CHAR(255) DEFAULT NULL,
    gwlist CHAR(255),
    sort_alg CHAR(1) DEFAULT 'N' NOT NULL,
    sort_profile INT(10) UNSIGNED DEFAULT NULL,
    attrs CHAR(255) DEFAULT NULL,
    description CHAR(128) DEFAULT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('dr_carriers','3') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS dr_carriers (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    carrierid CHAR(64) NOT NULL,
    gwlist CHAR(255) NOT NULL,
    flags INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    sort_alg CHAR(1) DEFAULT 'N' NOT NULL,
    state INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    attrs CHAR(255) DEFAULT NULL,
    description CHAR(128) DEFAULT NULL,
    CONSTRAINT dr_carrier_idx UNIQUE (carrierid)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('dr_groups','2') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS dr_groups (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    username CHAR(64) NOT NULL,
    domain CHAR(128) DEFAULT NULL,
    groupid INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    description CHAR(128) DEFAULT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('dr_partitions','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS dr_partitions (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    partition_name CHAR(255) NOT NULL,
    db_url CHAR(255) NOT NULL,
    drd_table CHAR(255),
    drr_table CHAR(255),
    drg_table CHAR(255),
    drc_table CHAR(255),
    ruri_avp CHAR(255),
    gw_id_avp CHAR(255),
    gw_priprefix_avp CHAR(255),
    gw_sock_avp CHAR(255),
    rule_id_avp CHAR(255),
    rule_prefix_avp CHAR(255),
    carrier_id_avp CHAR(255)
) ENGINE=InnoDB;


INSERT INTO version (table_name, table_version) values ('sockets','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS sockets (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    socket CHAR(128) NOT NULL,
    advertised CHAR(128) DEFAULT NULL,
    tag CHAR(128) DEFAULT NULL,
    flags CHAR(128) DEFAULT NULL,
    tos CHAR(32) DEFAULT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('domainpolicy','3') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS domainpolicy (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    rule CHAR(255) NOT NULL,
    type CHAR(255) NOT NULL,
    att CHAR(255),
    val CHAR(128),
    description CHAR(255) NOT NULL,
    CONSTRAINT rav_idx UNIQUE (rule, att, val)
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS rule_idx ON domainpolicy (rule);

INSERT INTO version (table_name, table_version) values ('config','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS config (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    name CHAR(255) NOT NULL,
    value TEXT(4096) DEFAULT NULL,
    description CHAR(255) DEFAULT NULL,
    CONSTRAINT name_idx UNIQUE (name)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('trie_table','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS trie_table (
    ruleid INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    prefix CHAR(64) NOT NULL,
    attrs CHAR(255) DEFAULT NULL,
    priority INT(11) DEFAULT 1 NOT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('trie_partitions','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS trie_partitions (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    partition_name CHAR(255) NOT NULL,
    db_url CHAR(255) NOT NULL,
    trie_table CHAR(255)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('acc','7') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS acc (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    method CHAR(16) DEFAULT '' NOT NULL,
    from_tag CHAR(64) DEFAULT '' NOT NULL,
    to_tag CHAR(64) DEFAULT '' NOT NULL,
    callid CHAR(64) DEFAULT '' NOT NULL,
    sip_code CHAR(3) DEFAULT '' NOT NULL,
    sip_reason CHAR(32) DEFAULT '' NOT NULL,
    time DATETIME NOT NULL,
    duration INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    ms_duration INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    setuptime INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    created DATETIME DEFAULT NULL
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS callid_idx ON acc (callid);

INSERT INTO version (table_name, table_version) values ('missed_calls','5') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS missed_calls (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    method CHAR(16) DEFAULT '' NOT NULL,
    from_tag CHAR(64) DEFAULT '' NOT NULL,
    to_tag CHAR(64) DEFAULT '' NOT NULL,
    callid CHAR(64) DEFAULT '' NOT NULL,
    sip_code CHAR(3) DEFAULT '' NOT NULL,
    sip_reason CHAR(32) DEFAULT '' NOT NULL,
    time DATETIME NOT NULL,
    setuptime INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    created DATETIME DEFAULT NULL
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS callid_idx ON missed_calls (callid);

INSERT INTO version (table_name, table_version) values ('carrierroute','3') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS carrierroute (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    carrier INT(10) UNSIGNED DEFAULT 0 NOT NULL,
    domain CHAR(64) DEFAULT '' NOT NULL,
    scan_prefix CHAR(64) DEFAULT '' NOT NULL,
    flags INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    mask INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    prob FLOAT DEFAULT 0 NOT NULL,
    strip INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    rewrite_host CHAR(255) DEFAULT '' NOT NULL,
    rewrite_prefix CHAR(64) DEFAULT '' NOT NULL,
    rewrite_suffix CHAR(64) DEFAULT '' NOT NULL,
    description CHAR(255) DEFAULT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('carrierfailureroute','2') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS carrierfailureroute (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    carrier INT(10) UNSIGNED DEFAULT 0 NOT NULL,
    domain CHAR(64) DEFAULT '' NOT NULL,
    scan_prefix CHAR(64) DEFAULT '' NOT NULL,
    host_name CHAR(255) DEFAULT '' NOT NULL,
    reply_code CHAR(3) DEFAULT '' NOT NULL,
    flags INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    mask INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    next_domain CHAR(64) DEFAULT '' NOT NULL,
    description CHAR(255) DEFAULT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('route_tree','2') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS route_tree (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    carrier CHAR(64) DEFAULT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('rtpengine','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS rtpengine (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    socket TEXT NOT NULL,
    set_id INT(10) UNSIGNED NOT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('cpl','2') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS cpl (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    username CHAR(64) NOT NULL,
    domain CHAR(64) DEFAULT '' NOT NULL,
    cpl_xml TEXT,
    cpl_bin TEXT,
    CONSTRAINT account_idx UNIQUE (username, domain)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('closeddial','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS closeddial (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    username CHAR(64) DEFAULT '' NOT NULL,
    domain CHAR(64) DEFAULT '' NOT NULL,
    cd_username CHAR(64) DEFAULT '' NOT NULL,
    cd_domain CHAR(64) DEFAULT '' NOT NULL,
    group_id CHAR(64) DEFAULT '' NOT NULL,
    new_uri CHAR(255) DEFAULT '' NOT NULL,
    CONSTRAINT cd_idx1 UNIQUE (username, domain, cd_domain, cd_username, group_id)
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS cd_idx2 ON closeddial (group_id);
CREATE INDEX IF NOT EXISTS cd_idx3 ON closeddial (cd_username);
CREATE INDEX IF NOT EXISTS cd_idx4 ON closeddial (username);

INSERT INTO version (table_name, table_version) values ('smpp','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS smpp (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    name CHAR(255) NOT NULL,
    ip CHAR(50) NOT NULL,
    port INT(5) UNSIGNED NOT NULL,
    system_id CHAR(16) NOT NULL,
    password CHAR(9) NOT NULL,
    system_type CHAR(13) DEFAULT '' NOT NULL,
    src_ton INT UNSIGNED DEFAULT 0 NOT NULL,
    src_npi INT UNSIGNED DEFAULT 0 NOT NULL,
    dst_ton INT UNSIGNED DEFAULT 0 NOT NULL,
    dst_npi INT UNSIGNED DEFAULT 0 NOT NULL,
    session_type INT UNSIGNED DEFAULT 1 NOT NULL,
    CONSTRAINT unique_name UNIQUE (name)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('load_balancer','3') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS load_balancer (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    group_id INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    dst_uri CHAR(128) NOT NULL,
    resources CHAR(255) NOT NULL,
    probe_mode INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    attrs CHAR(255) DEFAULT NULL,
    description CHAR(128) DEFAULT NULL
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS dsturi_idx ON load_balancer (dst_uri);

INSERT INTO version (table_name, table_version) values ('presentity','5') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS presentity (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    username CHAR(64) NOT NULL,
    domain CHAR(64) NOT NULL,
    event CHAR(64) NOT NULL,
    etag CHAR(64) NOT NULL,
    expires INT(11) NOT NULL,
    received_time INT(11) NOT NULL,
    body BLOB DEFAULT NULL,
    extra_hdrs BLOB DEFAULT NULL,
    sender CHAR(255) DEFAULT NULL,
    CONSTRAINT presentity_idx UNIQUE (username, domain, event, etag)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('active_watchers','12') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS active_watchers (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    presentity_uri CHAR(255) NOT NULL,
    watcher_username CHAR(64) NOT NULL,
    watcher_domain CHAR(64) NOT NULL,
    to_user CHAR(64) NOT NULL,
    to_domain CHAR(64) NOT NULL,
    event CHAR(64) DEFAULT 'presence' NOT NULL,
    event_id CHAR(64),
    to_tag CHAR(64) NOT NULL,
    from_tag CHAR(64) NOT NULL,
    callid CHAR(64) NOT NULL,
    local_cseq INT(11) NOT NULL,
    remote_cseq INT(11) NOT NULL,
    contact CHAR(255) NOT NULL,
    record_route TEXT,
    expires INT(11) NOT NULL,
    status INT(11) DEFAULT 2 NOT NULL,
    reason CHAR(64),
    version INT(11) DEFAULT 0 NOT NULL,
    socket_info CHAR(64) NOT NULL,
    local_contact CHAR(255) NOT NULL,
    sharing_tag CHAR(32) DEFAULT NULL,
    CONSTRAINT active_watchers_idx UNIQUE (presentity_uri, callid, to_tag, from_tag)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('watchers','4') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS watchers (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    presentity_uri CHAR(255) NOT NULL,
    watcher_username CHAR(64) NOT NULL,
    watcher_domain CHAR(64) NOT NULL,
    event CHAR(64) DEFAULT 'presence' NOT NULL,
    status INT(11) NOT NULL,
    reason CHAR(64),
    inserted_time INT(11) NOT NULL,
    CONSTRAINT watcher_idx UNIQUE (presentity_uri, watcher_username, watcher_domain, event)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('xcap','4') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS xcap (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    username CHAR(64) NOT NULL,
    domain CHAR(64) NOT NULL,
    doc LONGBLOB NOT NULL,
    doc_type INT(11) NOT NULL,
    etag CHAR(64) NOT NULL,
    source INT(11) NOT NULL,
    doc_uri CHAR(255) NOT NULL,
    port INT(11) NOT NULL,
    CONSTRAINT account_doc_type_idx UNIQUE (username, domain, doc_type, doc_uri)
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS source_idx ON xcap (source);

INSERT INTO version (table_name, table_version) values ('pua','9') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS pua (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    pres_uri CHAR(255) NOT NULL,
    pres_id CHAR(255) NOT NULL,
    event INT(11) NOT NULL,
    expires INT(11) NOT NULL,
    desired_expires INT(11) NOT NULL,
    flag INT(11) NOT NULL,
    etag CHAR(64),
    tuple_id CHAR(64),
    watcher_uri CHAR(255),
    to_uri CHAR(255),
    call_id CHAR(64),
    to_tag CHAR(64),
    from_tag CHAR(64),
    cseq INT(11),
    record_route TEXT,
    contact CHAR(255),
    remote_contact CHAR(255),
    version INT(11),
    extra_headers TEXT,
    sharing_tag CHAR(32) DEFAULT NULL
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS del1_idx ON pua (pres_uri, event);
CREATE INDEX IF NOT EXISTS del2_idx ON pua (expires);
CREATE INDEX IF NOT EXISTS update_idx ON pua (pres_uri, pres_id, flag, event);

INSERT INTO version (table_name, table_version) values ('clusterer','4') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS clusterer (
    id INT(10) AUTO_INCREMENT PRIMARY KEY NOT NULL,
    cluster_id INT(10) NOT NULL,
    node_id INT(10) NOT NULL,
    url CHAR(64) NOT NULL,
    state INT(1) DEFAULT 1 NOT NULL,
    no_ping_retries INT(10) DEFAULT 3 NOT NULL,
    priority INT(10) DEFAULT 50 NOT NULL,
    sip_addr CHAR(64),
    flags CHAR(64),
    description CHAR(64),
    CONSTRAINT clusterer_idx UNIQUE (cluster_id, node_id)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('tls_mgm','3') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS tls_mgm (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    domain CHAR(64) NOT NULL,
    match_ip_address CHAR(255) DEFAULT NULL,
    match_sip_domain CHAR(255) DEFAULT NULL,
    type INT(1) DEFAULT 1 NOT NULL,
    method CHAR(16) DEFAULT 'SSLv23',
    verify_cert INT(1) DEFAULT 1,
    require_cert INT(1) DEFAULT 1,
    certificate BLOB,
    private_key BLOB,
    crl_check_all INT(1) DEFAULT 0,
    crl_dir CHAR(255) DEFAULT NULL,
    ca_list MEDIUMBLOB DEFAULT NULL,
    ca_dir CHAR(255) DEFAULT NULL,
    cipher_list CHAR(255) DEFAULT NULL,
    dh_params BLOB DEFAULT NULL,
    ec_curve CHAR(255) DEFAULT NULL,
    CONSTRAINT domain_type_idx UNIQUE (domain, type)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('b2b_sca','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS b2b_sca (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    shared_line CHAR(64) NOT NULL,
    watchers CHAR(255) NOT NULL,
    app1_shared_entity INT(1) UNSIGNED DEFAULT NULL,
    app1_call_state INT(1) UNSIGNED DEFAULT NULL,
    app1_call_info_uri CHAR(255) DEFAULT NULL,
    app1_call_info_appearance_uri CHAR(255) DEFAULT NULL,
    app1_b2bl_key CHAR(64) DEFAULT NULL,
    app2_shared_entity INT(1) UNSIGNED DEFAULT NULL,
    app2_call_state INT(1) UNSIGNED DEFAULT NULL,
    app2_call_info_uri CHAR(255) DEFAULT NULL,
    app2_call_info_appearance_uri CHAR(255) DEFAULT NULL,
    app2_b2bl_key CHAR(64) DEFAULT NULL,
    app3_shared_entity INT(1) UNSIGNED DEFAULT NULL,
    app3_call_state INT(1) UNSIGNED DEFAULT NULL,
    app3_call_info_uri CHAR(255) DEFAULT NULL,
    app3_call_info_appearance_uri CHAR(255) DEFAULT NULL,
    app3_b2bl_key CHAR(64) DEFAULT NULL,
    app4_shared_entity INT(1) UNSIGNED DEFAULT NULL,
    app4_call_state INT(1) UNSIGNED DEFAULT NULL,
    app4_call_info_uri CHAR(255) DEFAULT NULL,
    app4_call_info_appearance_uri CHAR(255) DEFAULT NULL,
    app4_b2bl_key CHAR(64) DEFAULT NULL,
    app5_shared_entity INT(1) UNSIGNED DEFAULT NULL,
    app5_call_state INT(1) UNSIGNED DEFAULT NULL,
    app5_call_info_uri CHAR(255) DEFAULT NULL,
    app5_call_info_appearance_uri CHAR(255) DEFAULT NULL,
    app5_b2bl_key CHAR(64) DEFAULT NULL,
    app6_shared_entity INT(1) UNSIGNED DEFAULT NULL,
    app6_call_state INT(1) UNSIGNED DEFAULT NULL,
    app6_call_info_uri CHAR(255) DEFAULT NULL,
    app6_call_info_appearance_uri CHAR(255) DEFAULT NULL,
    app6_b2bl_key CHAR(64) DEFAULT NULL,
    app7_shared_entity INT(1) UNSIGNED DEFAULT NULL,
    app7_call_state INT(1) UNSIGNED DEFAULT NULL,
    app7_call_info_uri CHAR(255) DEFAULT NULL,
    app7_call_info_appearance_uri CHAR(255) DEFAULT NULL,
    app7_b2bl_key CHAR(64) DEFAULT NULL,
    app8_shared_entity INT(1) UNSIGNED DEFAULT NULL,
    app8_call_state INT(1) UNSIGNED DEFAULT NULL,
    app8_call_info_uri CHAR(255) DEFAULT NULL,
    app8_call_info_appearance_uri CHAR(255) DEFAULT NULL,
    app8_b2bl_key CHAR(64) DEFAULT NULL,
    app9_shared_entity INT(1) UNSIGNED DEFAULT NULL,
    app9_call_state INT(1) UNSIGNED DEFAULT NULL,
    app9_call_info_uri CHAR(255) DEFAULT NULL,
    app9_call_info_appearance_uri CHAR(255) DEFAULT NULL,
    app9_b2bl_key CHAR(64) DEFAULT NULL,
    app10_shared_entity INT(1) UNSIGNED DEFAULT NULL,
    app10_call_state INT(1) UNSIGNED DEFAULT NULL,
    app10_call_info_uri CHAR(255) DEFAULT NULL,
    app10_call_info_appearance_uri CHAR(255) DEFAULT NULL,
    app10_b2bl_key CHAR(64) DEFAULT NULL,
    CONSTRAINT sca_idx UNIQUE (shared_line)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('freeswitch','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS freeswitch (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    username CHAR(64),
    password CHAR(64) NOT NULL,
    ip CHAR(20) NOT NULL,
    port INT(11) DEFAULT 8021 NOT NULL,
    events_csv CHAR(255)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('silo','6') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS silo (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    src_addr CHAR(255) DEFAULT '' NOT NULL,
    dst_addr CHAR(255) DEFAULT '' NOT NULL,
    username CHAR(64) DEFAULT '' NOT NULL,
    domain CHAR(64) DEFAULT '' NOT NULL,
    inc_time INT DEFAULT 0 NOT NULL,
    exp_time INT DEFAULT 0 NOT NULL,
    snd_time INT DEFAULT 0 NOT NULL,
    ctype CHAR(255) DEFAULT NULL,
    body BLOB DEFAULT NULL
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS account_idx ON silo (username, domain);

INSERT INTO version (table_name, table_version) values ('cachedb','2') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS cachedb (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    keyname CHAR(255) NOT NULL,
    value TEXT(512) NOT NULL,
    counter INT(10) DEFAULT 0 NOT NULL,
    expires INT(10) UNSIGNED DEFAULT 0 NOT NULL,
    CONSTRAINT cachedbsql_keyname_idx UNIQUE (keyname)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('rls_presentity','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS rls_presentity (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    rlsubs_did CHAR(255) NOT NULL,
    resource_uri CHAR(255) NOT NULL,
    content_type CHAR(255) NOT NULL,
    presence_state BLOB NOT NULL,
    expires INT(11) NOT NULL,
    updated INT(11) NOT NULL,
    auth_state INT(11) NOT NULL,
    reason CHAR(64) NOT NULL,
    CONSTRAINT rls_presentity_idx UNIQUE (rlsubs_did, resource_uri)
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS updated_idx ON rls_presentity (updated);

INSERT INTO version (table_name, table_version) values ('rls_watchers','2') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS rls_watchers (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    presentity_uri CHAR(255) NOT NULL,
    to_user CHAR(64) NOT NULL,
    to_domain CHAR(64) NOT NULL,
    watcher_username CHAR(64) NOT NULL,
    watcher_domain CHAR(64) NOT NULL,
    event CHAR(64) DEFAULT 'presence' NOT NULL,
    event_id CHAR(64),
    to_tag CHAR(64) NOT NULL,
    from_tag CHAR(64) NOT NULL,
    callid CHAR(64) NOT NULL,
    local_cseq INT(11) NOT NULL,
    remote_cseq INT(11) NOT NULL,
    contact CHAR(64) NOT NULL,
    record_route TEXT,
    expires INT(11) NOT NULL,
    status INT(11) DEFAULT 2 NOT NULL,
    reason CHAR(64) NOT NULL,
    version INT(11) DEFAULT 0 NOT NULL,
    socket_info CHAR(64) NOT NULL,
    local_contact CHAR(255) NOT NULL,
    CONSTRAINT rls_watcher_idx UNIQUE (presentity_uri, callid, to_tag, from_tag)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('jwt_profiles','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS jwt_profiles (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    tag CHAR(128) NOT NULL,
    sip_username CHAR(128) NOT NULL,
    CONSTRAINT jwt_tag_idx UNIQUE (tag)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('jwt_secrets','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS jwt_secrets (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    corresponding_tag CHAR(128) NOT NULL,
    secret TEXT NOT NULL,
    start_ts INT NOT NULL,
    end_ts INT NOT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('dbaliases','2') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS dbaliases (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    alias_username CHAR(64) DEFAULT '' NOT NULL,
    alias_domain CHAR(64) DEFAULT '' NOT NULL,
    username CHAR(64) DEFAULT '' NOT NULL,
    domain CHAR(64) DEFAULT '' NOT NULL,
    CONSTRAINT alias_idx UNIQUE (alias_username, alias_domain)
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS target_idx ON dbaliases (username, domain);

INSERT INTO version (table_name, table_version) values ('speed_dial','3') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS speed_dial (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    username CHAR(64) DEFAULT '' NOT NULL,
    domain CHAR(64) DEFAULT '' NOT NULL,
    sd_username CHAR(64) DEFAULT '' NOT NULL,
    sd_domain CHAR(64) DEFAULT '' NOT NULL,
    new_uri CHAR(255) DEFAULT '' NOT NULL,
    fname CHAR(64) DEFAULT '' NOT NULL,
    lname CHAR(64) DEFAULT '' NOT NULL,
    description CHAR(64) DEFAULT '' NOT NULL,
    CONSTRAINT speed_dial_idx UNIQUE (username, domain, sd_domain, sd_username)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('fraud_detection','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS fraud_detection (
    ruleid INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    profileid INT UNSIGNED NOT NULL,
    prefix CHAR(64) NOT NULL,
    start_hour CHAR(5) DEFAULT '00:00' NOT NULL,
    end_hour CHAR(5) DEFAULT '23:59' NOT NULL,
    daysoftheweek CHAR(64) DEFAULT 'Mon-Sun' NOT NULL,
    cpm_warning INT(5) UNSIGNED DEFAULT 0 NOT NULL,
    cpm_critical INT(5) UNSIGNED DEFAULT 0 NOT NULL,
    call_duration_warning INT(5) UNSIGNED DEFAULT 0 NOT NULL,
    call_duration_critical INT(5) UNSIGNED DEFAULT 0 NOT NULL,
    total_calls_warning INT(5) UNSIGNED DEFAULT 0 NOT NULL,
    total_calls_critical INT(5) UNSIGNED DEFAULT 0 NOT NULL,
    concurrent_calls_warning INT(5) UNSIGNED DEFAULT 0 NOT NULL,
    concurrent_calls_critical INT(5) UNSIGNED DEFAULT 0 NOT NULL,
    sequential_calls_warning INT(5) UNSIGNED DEFAULT 0 NOT NULL,
    sequential_calls_critical INT(5) UNSIGNED DEFAULT 0 NOT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('registrant','3') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS registrant (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    registrar CHAR(255) DEFAULT '' NOT NULL,
    proxy CHAR(255) DEFAULT NULL,
    aor CHAR(255) DEFAULT '' NOT NULL,
    third_party_registrant CHAR(255) DEFAULT NULL,
    username CHAR(64) DEFAULT NULL,
    password CHAR(64) DEFAULT NULL,
    binding_URI CHAR(255) DEFAULT '' NOT NULL,
    binding_params CHAR(64) DEFAULT NULL,
    expiry INT(1) UNSIGNED DEFAULT NULL,
    forced_socket CHAR(64) DEFAULT NULL,
    cluster_shtag CHAR(64) DEFAULT NULL,
    state INT DEFAULT 0 NOT NULL,
    CONSTRAINT registrant_idx UNIQUE (aor, binding_URI, registrar)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('grp','3') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS grp (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    username CHAR(64) DEFAULT '' NOT NULL,
    domain CHAR(64) DEFAULT '' NOT NULL,
    grp CHAR(64) DEFAULT '' NOT NULL,
    last_modified DATETIME DEFAULT '1900-01-01 00:00:01' NOT NULL,
    CONSTRAINT account_group_idx UNIQUE (username, domain, grp)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('re_grp','2') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS re_grp (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    reg_exp CHAR(128) DEFAULT '' NOT NULL,
    group_id INT(11) DEFAULT 0 NOT NULL
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS group_idx ON re_grp (group_id);

INSERT INTO version (table_name, table_version) values ('cc_flows','2') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS cc_flows (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    flowid CHAR(64) NOT NULL,
    priority INT(11) UNSIGNED DEFAULT 256 NOT NULL,
    skill CHAR(64) NOT NULL,
    prependcid CHAR(32) DEFAULT NULL,
    max_wrapup_time INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    dissuading_hangup INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    dissuading_onhold_th INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    dissuading_ewt_th INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    dissuading_qsize_th INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    message_welcome CHAR(128) DEFAULT NULL,
    message_queue CHAR(128) NOT NULL,
    message_dissuading CHAR(128) DEFAULT NULL,
    message_flow_id CHAR(128) DEFAULT NULL,
    CONSTRAINT unique_flowid UNIQUE (flowid)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('cc_agents','3') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS cc_agents (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    agentid CHAR(128) NOT NULL,
    location CHAR(128),
    logstate INT(10) UNSIGNED DEFAULT 0 NOT NULL,
    msrp_location CHAR(128),
    msrp_max_sessions INT(10) UNSIGNED DEFAULT 4 NOT NULL,
    skills CHAR(255) NOT NULL,
    wrapup_end_time INT(11) DEFAULT 0 NOT NULL,
    wrapup_time INT(11) DEFAULT 0 NOT NULL,
    CONSTRAINT unique_agentid UNIQUE (agentid)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('cc_cdrs','2') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS cc_cdrs (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    caller CHAR(64) NOT NULL,
    received_timestamp DATETIME NOT NULL,
    wait_time INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    pickup_time INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    talk_time INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    flow_id CHAR(128) NOT NULL,
    agent_id CHAR(128) DEFAULT NULL,
    call_type INT(11) DEFAULT -1 NOT NULL,
    rejected INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    fstats INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    cid INT(11) UNSIGNED DEFAULT 0,
    media INT(11) DEFAULT 0 NOT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('cc_calls','3') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS cc_calls (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    state INT(11) NOT NULL,
    media INT(11) NOT NULL,
    ig_cback INT(11) NOT NULL,
    no_rej INT(11) NOT NULL,
    setup_time INT(11) NOT NULL,
    eta INT(11) NOT NULL,
    last_start INT(11) NOT NULL,
    recv_time INT(11) NOT NULL,
    caller_dn CHAR(128) NOT NULL,
    caller_un CHAR(128) NOT NULL,
    b2buaid CHAR(128) DEFAULT '' NOT NULL,
    flow CHAR(128) NOT NULL,
    agent CHAR(128) NOT NULL,
    script_param CHAR(128) NOT NULL,
    CONSTRAINT unique_id UNIQUE (b2buaid)
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS b2buaid_idx ON cc_calls (b2buaid);

INSERT INTO version (table_name, table_version) values ('subscriber','8') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS subscriber (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    username CHAR(64) DEFAULT '' NOT NULL,
    domain CHAR(64) DEFAULT '' NOT NULL,
    password CHAR(25) DEFAULT '' NOT NULL,
    ha1 CHAR(64) DEFAULT '' NOT NULL,
    ha1_sha256 CHAR(64) DEFAULT '' NOT NULL,
    ha1_sha512t256 CHAR(64) DEFAULT '' NOT NULL,
    CONSTRAINT account_idx UNIQUE (username, domain)
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS username_idx ON subscriber (username);

INSERT INTO version (table_name, table_version) values ('uri','2') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS uri (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    username CHAR(64) DEFAULT '' NOT NULL,
    domain CHAR(64) DEFAULT '' NOT NULL,
    uri_user CHAR(64) DEFAULT '' NOT NULL,
    last_modified DATETIME DEFAULT '1900-01-01 00:00:01' NOT NULL,
    CONSTRAINT account_idx UNIQUE (username, domain, uri_user)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('usr_preferences','3') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS usr_preferences (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    uuid CHAR(64) DEFAULT '' NOT NULL,
    username CHAR(64) DEFAULT 0 NOT NULL,
    domain CHAR(64) DEFAULT '' NOT NULL,
    attribute CHAR(32) DEFAULT '' NOT NULL,
    type INT(11) DEFAULT 0 NOT NULL,
    value CHAR(128) DEFAULT '' NOT NULL,
    last_modified DATETIME DEFAULT '1900-01-01 00:00:01' NOT NULL
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS ua_idx ON usr_preferences (uuid, attribute);
CREATE INDEX IF NOT EXISTS uda_idx ON usr_preferences (username, domain, attribute);
CREATE INDEX IF NOT EXISTS value_idx ON usr_preferences (value);

INSERT INTO version (table_name, table_version) values ('janus','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS janus (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    janus_id TEXT NOT NULL,
    janus_url TEXT NOT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('dispatcher','9') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS dispatcher (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    setid INT DEFAULT 0 NOT NULL,
    destination CHAR(192) DEFAULT '' NOT NULL,
    socket CHAR(128) DEFAULT NULL,
    state INT DEFAULT 0 NOT NULL,
    probe_mode INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    weight CHAR(64) DEFAULT 1 NOT NULL,
    priority INT DEFAULT 0 NOT NULL,
    attrs CHAR(128) DEFAULT NULL,
    description CHAR(64) DEFAULT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('qr_profiles','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS qr_profiles (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    profile_name CHAR(64) NOT NULL,
    warn_threshold_asr DOUBLE DEFAULT -1 NOT NULL,
    warn_threshold_ccr DOUBLE DEFAULT -1 NOT NULL,
    warn_threshold_pdd DOUBLE DEFAULT -1 NOT NULL,
    warn_threshold_ast DOUBLE DEFAULT -1 NOT NULL,
    warn_threshold_acd DOUBLE DEFAULT -1 NOT NULL,
    crit_threshold_asr DOUBLE DEFAULT -1 NOT NULL,
    crit_threshold_ccr DOUBLE DEFAULT -1 NOT NULL,
    crit_threshold_pdd DOUBLE DEFAULT -1 NOT NULL,
    crit_threshold_ast DOUBLE DEFAULT -1 NOT NULL,
    crit_threshold_acd DOUBLE DEFAULT -1 NOT NULL,
    warn_penalty_asr DOUBLE DEFAULT 0.5 NOT NULL,
    warn_penalty_ccr DOUBLE DEFAULT 0.5 NOT NULL,
    warn_penalty_pdd DOUBLE DEFAULT 0.5 NOT NULL,
    warn_penalty_ast DOUBLE DEFAULT 0.5 NOT NULL,
    warn_penalty_acd DOUBLE DEFAULT 0.5 NOT NULL,
    crit_penalty_asr DOUBLE DEFAULT 0.05 NOT NULL,
    crit_penalty_ccr DOUBLE DEFAULT 0.05 NOT NULL,
    crit_penalty_pdd DOUBLE DEFAULT 0.05 NOT NULL,
    crit_penalty_ast DOUBLE DEFAULT 0.05 NOT NULL,
    crit_penalty_acd DOUBLE DEFAULT 0.05 NOT NULL
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('rc_clients','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS rc_clients (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    client_id CHAR(64) NOT NULL,
    wholesale_rate INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    retail_rate INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    CONSTRAINT client_id_idx UNIQUE (client_id)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('rc_vendors','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS rc_vendors (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    vendor_id CHAR(64) NOT NULL,
    vendor_rate INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    CONSTRAINT vendor_id_idx UNIQUE (vendor_id)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('rc_ratesheets','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS rc_ratesheets (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    ratesheet_table CHAR(64) NOT NULL,
    currency CHAR(64) NOT NULL,
    CONSTRAINT table_idx UNIQUE (ratesheet_table)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('rc_demo_ratesheet','1') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS rc_demo_ratesheet (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    prefix CHAR(64) NOT NULL,
    destination CHAR(128) NOT NULL,
    price FLOAT DEFAULT 0 NOT NULL,
    minimum INT(11) UNSIGNED DEFAULT 0 NOT NULL,
    increment INT(11) UNSIGNED DEFAULT 1 NOT NULL,
    CONSTRAINT prefix_idx UNIQUE (prefix)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('imc_rooms','2') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS imc_rooms (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    name CHAR(64) NOT NULL,
    domain CHAR(64) NOT NULL,
    flag INT(11) NOT NULL,
    CONSTRAINT name_domain_idx UNIQUE (name, domain)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('imc_members','2') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS imc_members (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    username CHAR(64) NOT NULL,
    domain CHAR(64) NOT NULL,
    room CHAR(64) NOT NULL,
    flag INT(11) NOT NULL,
    CONSTRAINT account_room_idx UNIQUE (username, domain, room)
) ENGINE=InnoDB;

INSERT INTO version (table_name, table_version) values ('sip_trace','5') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS sip_trace (
    id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
    time_stamp DATETIME DEFAULT '1900-01-01 00:00:01' NOT NULL,
    callid CHAR(255) DEFAULT '' NOT NULL,
    trace_attrs CHAR(255) DEFAULT NULL,
    msg TEXT NOT NULL,
    method CHAR(32) DEFAULT '' NOT NULL,
    status CHAR(255) DEFAULT NULL,
    from_proto CHAR(5) NOT NULL,
    from_ip CHAR(50) DEFAULT '' NOT NULL,
    from_port INT(5) UNSIGNED NOT NULL,
    to_proto CHAR(5) NOT NULL,
    to_ip CHAR(50) DEFAULT '' NOT NULL,
    to_port INT(5) UNSIGNED NOT NULL,
    fromtag CHAR(64) DEFAULT '' NOT NULL,
    direction CHAR(4) DEFAULT '' NOT NULL
) ENGINE=InnoDB;

CREATE INDEX IF NOT EXISTS trace_attrs_idx ON sip_trace (trace_attrs);
CREATE INDEX IF NOT EXISTS date_idx ON sip_trace (time_stamp);
CREATE INDEX IF NOT EXISTS fromip_idx ON sip_trace (from_ip);
CREATE INDEX IF NOT EXISTS callid_idx ON sip_trace (callid);

INSERT INTO version (table_name, table_version) values ('dialog','12') ON DUPLICATE KEY UPDATE table_version = VALUES(table_version);
CREATE TABLE IF NOT EXISTS dialog (
    dlg_id BIGINT(10) UNSIGNED PRIMARY KEY NOT NULL,
    callid CHAR(255) NOT NULL,
    from_uri CHAR(255) NOT NULL,
    from_tag CHAR(64) NOT NULL,
    to_uri CHAR(255) NOT NULL,
    to_tag CHAR(64) NOT NULL,
    mangled_from_uri CHAR(255) DEFAULT NULL,
    mangled_to_uri CHAR(255) DEFAULT NULL,
    caller_cseq CHAR(11) NOT NULL,
    callee_cseq CHAR(11) NOT NULL,
    caller_ping_cseq INT(11) UNSIGNED NOT NULL,
    callee_ping_cseq INT(11) UNSIGNED NOT NULL,
    caller_route_set TEXT(512),
    callee_route_set TEXT(512),
    caller_contact CHAR(255),
    callee_contact CHAR(255),
    caller_sock CHAR(64) NOT NULL,
    callee_sock CHAR(64) NOT NULL,
    state INT(10) UNSIGNED NOT NULL,
    start_time INT(10) UNSIGNED NOT NULL,
    timeout INT(10) UNSIGNED NOT NULL,
    vars BLOB(4096) DEFAULT NULL,
    profiles TEXT(512) DEFAULT NULL,
    script_flags CHAR(255) DEFAULT NULL,
    module_flags INT(10) UNSIGNED DEFAULT 0 NOT NULL,
    flags INT(10) UNSIGNED DEFAULT 0 NOT NULL,
    rt_on_answer CHAR(64) DEFAULT NULL,
    rt_on_timeout CHAR(64) DEFAULT NULL,
    rt_on_hangup CHAR(64) DEFAULT NULL
) ENGINE=InnoDB;
