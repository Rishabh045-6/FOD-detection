export const formatNullableNumber = (
  value: number | null,
  digits: number,
  suffix = ''
): string => {
  if (value == null) {
    return 'N/A';
  }

  return `${value.toFixed(digits)}${suffix}`;
};
