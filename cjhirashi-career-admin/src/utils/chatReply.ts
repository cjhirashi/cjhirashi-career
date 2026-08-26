const THINK_BLOCK = /<\s*(thinking|think)\s*>[\s\S]*?<\s*\/\s*\1\s*>/gi
const UNCLOSED_THINK = /<\s*(thinking|think)\s*>[\s\S]*/gi
const THINK_TAG = /<\s*\/?\s*(thinking|think)\s*>/gi

/** Hide model chain-of-thought tags that leak into Bedrock assistant text. */
export function sanitizeAssistantReply(text: string): string {
  if (!text) return ''

  const withoutBlocks = text.replace(THINK_BLOCK, '')
  const withoutUnclosed = withoutBlocks.replace(UNCLOSED_THINK, '')
  const cleaned = withoutUnclosed.trim()
  if (cleaned) return cleaned
  return text.replace(THINK_TAG, '').trim()
}
