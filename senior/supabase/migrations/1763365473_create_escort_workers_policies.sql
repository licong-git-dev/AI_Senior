-- Migration: create_escort_workers_policies
-- Created at: 1763365473

-- Create policies for escort_workers table
CREATE POLICY "Enable read access for all users" ON escort_workers FOR SELECT USING (true);
CREATE POLICY "Enable insert for authenticated users" ON escort_workers FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for authenticated users" ON escort_workers FOR UPDATE USING (true);
CREATE POLICY "Enable delete for authenticated users" ON escort_workers FOR DELETE USING (true);;