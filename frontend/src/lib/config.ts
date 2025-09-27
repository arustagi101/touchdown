export function getOutputPath(): string {
  const path = process.env.NEXT_PUBLIC_OUTPUT_PATH || './output'
  return path
}

export function validateConfig(): { isValid: boolean; errors: string[] } {
  const errors: string[] = []

  if (!process.env.NEXT_PUBLIC_OUTPUT_PATH) {
    errors.push('NEXT_PUBLIC_OUTPUT_PATH environment variable is required')
  }

  return {
    isValid: errors.length === 0,
    errors
  }
}