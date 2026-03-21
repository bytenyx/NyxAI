export interface Knowledge {
  id: string
  title: string
  content?: string
  knowledge_type: string
  file_url?: string
  file_name?: string
  tags: string[]
  category?: string
  reference_count: number
  created_at: string
  updated_at: string
}

export interface KnowledgeCreate {
  title: string
  content?: string
  type?: 'text' | 'file'
  tags?: string[]
  category?: string
}

export interface KnowledgeUpdate {
  title?: string
  content?: string
  tags?: string[]
  category?: string
}
