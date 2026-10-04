export interface Thread {
  id: string;
  other_user_id: string;
  other_display_name: string;
  last_message: string | null;
  last_message_at: string | null;
}

export interface ChatMessage {
  id: string;
  sender_id: string;
  content: string;
  sent_at: string;
}