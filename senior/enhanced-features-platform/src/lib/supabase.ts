// Temporary mock supabase client to avoid build issues
const supabaseUrl = "https://bmaarkhvsuqsnvvbtcsa.supabase.co"
const supabaseAnonKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtYWFya2h2c3Vxc252dmJ0Y3NhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIzMTc5MzQsImV4cCI6MjA3Nzg5MzkzNH0.kc3ecE-L5VUjiaM46H0Q90Z65KoHROsAXE7zTp3HgFw"

// Mock supabase client
export const supabase = {
  functions: {
    invoke: async (functionName: string, options: any) => {
      if (functionName === 'voice-assistant') {
        try {
          const response = await fetch(`${supabaseUrl}/functions/v1/voice-assistant`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${supabaseAnonKey}`,
              'apikey': supabaseAnonKey
            },
            body: JSON.stringify(options.body)
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const data = await response.json();
          return { data, error: null };
        } catch (error) {
          return { data: null, error };
        }
      }
      return { data: null, error: new Error('Unknown function') };
    }
  }
};

// Helper function to invoke voice assistant
export const invokeVoiceAssistant = async (payload: any) => {
  const { data, error } = await supabase.functions.invoke('voice-assistant', {
    body: payload
  });

  if (error) {
    throw new Error((error as Error).message);
  }

  return data;
}
