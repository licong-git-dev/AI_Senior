-- Migration: create_payment_tables
-- Created at: 1763366831

-- 支付记录表
CREATE TABLE IF NOT EXISTS payment_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL,
  user_id UUID NOT NULL,
  payment_method VARCHAR(50) NOT NULL,
  payment_channel VARCHAR(50),
  amount DECIMAL(10,2) NOT NULL,
  currency VARCHAR(10) DEFAULT 'CNY',
  payment_status VARCHAR(50) DEFAULT 'pending',
  transaction_id VARCHAR(200),
  payment_time TIMESTAMP,
  refund_status VARCHAR(50),
  refund_amount DECIMAL(10,2),
  refund_time TIMESTAMP,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 结算记录表
CREATE TABLE IF NOT EXISTS settlement_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  worker_id UUID NOT NULL,
  order_id UUID NOT NULL,
  settlement_amount DECIMAL(10,2) NOT NULL,
  platform_fee DECIMAL(10,2) DEFAULT 0,
  worker_earnings DECIMAL(10,2) NOT NULL,
  settlement_status VARCHAR(50) DEFAULT 'pending',
  settlement_time TIMESTAMP,
  bank_account VARCHAR(100),
  bank_name VARCHAR(100),
  transaction_reference VARCHAR(200),
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE payment_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE settlement_records ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Enable read access for all users" ON payment_records FOR SELECT USING (true);
CREATE POLICY "Enable insert for authenticated users" ON payment_records FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for authenticated users" ON payment_records FOR UPDATE USING (true);

CREATE POLICY "Enable read access for all users" ON settlement_records FOR SELECT USING (true);
CREATE POLICY "Enable insert for authenticated users" ON settlement_records FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for authenticated users" ON settlement_records FOR UPDATE USING (true);;