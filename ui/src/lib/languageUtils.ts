// Arabic Unicode range detection
const arabicRegex = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/;

export function detectLanguageDirection(text: string): 'rtl' | 'ltr' {
  // Count Arabic characters
  const arabicMatches = text.match(arabicRegex);
  const arabicCount = arabicMatches ? arabicMatches.length : 0;
  
  // If more than 30% of the text is Arabic, treat as RTL
  const totalChars = text.replace(/\s/g, '').length;
  const arabicRatio = totalChars > 0 ? arabicCount / totalChars : 0;
  
  return arabicRatio > 0.3 ? 'rtl' : 'ltr';
}

export function isArabic(text: string): boolean {
  return detectLanguageDirection(text) === 'rtl';
}
