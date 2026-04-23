CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    device_name VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(100),
    serial_number VARCHAR(100) UNIQUE,
    mac_address VARCHAR(17),
    firmware_version VARCHAR(50),
    battery_level DECIMAL(5,2),
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    connection_status INTEGER DEFAULT 0,
    configuration JSONB DEFAULT '{}'::jsonb,
    geo_region VARCHAR(20) DEFAULT '420102',
    status INTEGER DEFAULT 1,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);