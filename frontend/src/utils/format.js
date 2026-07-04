// 1234567 -> "1.23M"
export function formatNumberWithSuffix(number) {
  const suffixes = ['', 'K', 'M', 'B', 'T'];
  let value = Number(number) || 0;
  let suffixIndex = 0;
  while (value >= 1000 && suffixIndex < suffixes.length - 1) {
    value /= 1000;
    suffixIndex++;
  }
  return value.toFixed(2) + suffixes[suffixIndex];
}
