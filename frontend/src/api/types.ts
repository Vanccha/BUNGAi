export interface Bungalow {
  id: number
  slug: string
  name: string
  short_description: string
  description: string
  capacity: number
  bedrooms: number
  size_m2: number
  price_per_night: number
  amenities: string[]
  images: string[]
  is_active: boolean
}

export type KnowledgeMode = 'always' | 'search'
export type IndexStatus = 'indexed' | 'pending' | 'error' | 'not_applicable'

export interface KnowledgeEntry {
  id: number
  category: string
  title: string
  content: string
  is_active: boolean
  sort_order: number
  updated_at: string
  mode: KnowledgeMode
  index_status: IndexStatus
  chunk_count: number
}

export interface Settings {
  resort_name: string
  tagline: string
  phone: string
  email: string
  address: string
  check_in_time: string
  check_out_time: string
  map_embed_url: string
  bot_name: string
  bot_welcome_message: string
  bot_extra_instructions: string
  // Sesli asistan
  voice_enabled: boolean
  voice_greeting: string
  voice_max_session_seconds: number
  voice_model: string
  voice_name: string
  voice_vad_eagerness: 'low' | 'medium' | 'high'
  voice_speed: number
  voice_lexicon_json: string
}

export type PublicSettings = Pick<Settings,
  'resort_name' | 'tagline' | 'phone' | 'email' | 'address' | 'check_in_time' | 'check_out_time' | 'map_embed_url' |
  'bot_name' | 'bot_welcome_message' | 'voice_enabled' | 'voice_greeting' | 'voice_max_session_seconds'>

export type ReservationStatus = 'pending_payment' | 'confirmed' | 'cancelled' | 'payment_failed'

export interface Reservation {
  id: number
  code: string
  bungalow_id: number
  bungalow_name: string
  guest_name: string
  guest_email: string
  guest_phone: string
  check_in: string
  check_out: string
  guests: number
  nights: number
  total_price: number
  note: string | null
  status: ReservationStatus
  source: 'web' | 'chatbot' | 'voice'
  created_at: string
}

export interface Payment {
  token: string
  reservation_code: string
  amount: number
  status: 'initialized' | 'success' | 'failure'
  created_at: string
}

export interface Availability {
  available: boolean
  nights: number
  total_price: number
}

export interface ReservationCreate {
  bungalow_id: number
  guest_name: string
  guest_email: string
  guest_phone: string
  check_in: string
  check_out: string
  guests: number
  note?: string
}

export interface PaymentInit {
  token: string
  amount: number
  payment_page_url: string
}

export interface PaymentInfo {
  token: string
  amount: number
  status: Payment['status']
  reservation: Reservation
}

export interface CardData {
  card_holder: string
  card_number: string
  expire_month: string
  expire_year: string
  cvc: string
}

export interface PaymentResult {
  status: 'success' | 'failure'
  message: string
  reservation: Reservation
}

export type ChatAction =
  | { type: 'payment_link'; reservation_code: string; url: string; amount: number }
  | { type: 'reservation_summary'; reservation: Reservation }

export interface ChatResponse {
  session_id: string
  reply: string
  actions: ChatAction[]
}

export interface SearchHit {
  entry_id: number
  entry_title: string
  category: string
  chunk_index: number
  text: string
  vector_score: number | null
  keyword_score: number | null
  vector_rank: number | null
  keyword_rank: number | null
  fused_score: number
}

export interface SearchTrace {
  query: string
  normalized_query: string
  results: SearchHit[]
  below_threshold: boolean
}

export interface RagStats {
  always_entries: number
  always_tokens: number
  always_token_limit: number
  search_entries: number
  chunks: number
  indexed_entries: number
  pending_entries: number
  error_entries: number
  embedding_model: string
  embeddings_enabled: boolean
  last_indexed_at: string | null
}

export interface AdminChatResponse extends ChatResponse {
  debug?: { searches: SearchTrace[] }
}

export type KnowledgeInput = Pick<KnowledgeEntry, 'category' | 'title' | 'content' | 'is_active' | 'sort_order' | 'mode'>

export interface AdminStats {
  total_reservations: number
  confirmed: number
  pending: number
  revenue_confirmed: number
  upcoming_checkins: Reservation[]
}

// ---- Sesli asistan ----
export interface VoiceSessionInfo {
  client_secret: string
  expires_at: number
  model: string
  session_id: string
  max_seconds: number
  greeting: string
}

export interface VoiceActionsResponse { actions: ChatAction[]; next: number; ended: boolean }

export interface VoiceTurn {
  role: 'user' | 'assistant' | 'tool'
  text: string
  ts: string
  name?: string
  arguments?: string
  output?: string
  ms?: number
  typed?: boolean
}

export interface VoiceSessionListItem {
  id: number
  session_id: string
  model: string
  voice: string
  status: 'created' | 'active' | 'ended' | 'error'
  started_at: string
  ended_at: string | null
  duration_seconds: number
  turn_count: number
  first_user_text: string
  reservation_codes: string[]
}

export interface VoiceSessionDetail extends VoiceSessionListItem {
  call_id: string | null
  transcript: VoiceTurn[]
}
