import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://bmaarkhvsuqsnvvbtcsa.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtYWFya2h2c3Vxc252dmJ0Y3NhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIzMTc5MzQsImV4cCI6MjA3Nzg5MzkzNH0.kc3ecE-L5VUjiaM46H0Q90Z65KoHROsAXE7zTp3HgFw'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
