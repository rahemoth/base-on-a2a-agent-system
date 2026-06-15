/**
 * Strip XML/HTML tags from a string.
 */
export function stripTags(str) {
  if (typeof str !== 'string') return '';
  return str.replace(/<[^>]*>/g, '');
}
