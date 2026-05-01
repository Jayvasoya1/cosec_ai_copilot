/**
 * response_codes.js — COSEC device API response code lookup table
 *
 * Usage:
 *   RESPONSE_CODES[code]          → description string (or undefined)
 *   getResponseDesc(code)         → string (falls back to "Unknown error")
 *   isSuccessCode(code)           → true when code === 0
 */

const RESPONSE_CODES = {
  0:  'Successful',
  1:  'Failed — Invalid Login Credentials',
  2:  'Date and time — manual set failed',
  3:  'Invalid Date/Time',
  4:  'Maximum users are already configured',
  5:  'Image — size is too big',
  6:  'Image — format not supported',
  7:  'Card 1 and Card 2 are identical',
  8:  'Card ID already exists',
  9:  'Fingerprint / Palm / Face template already exists',
  10: 'No Record Found',
  11: 'Template size / format mismatch',
  12: 'FP Memory full',
  13: 'User ID / Reference ID not found',
  14: 'Credential limit reached',
  15: 'Reader mismatch / Reader not configured',
  16: 'Device Busy',
  17: 'Internal process error',
  18: 'PIN already exists',
  19: 'Biometric credential not found',
  20: 'Memory Card Not Found',
  21: 'Reference User ID already exists',
  22: 'Wrong Selection',
  23: 'Palm template mode mismatch',
  24: 'Feature not enabled in config',
  25: 'Message already exists for same user on same date',
  26: 'Error in import data',
  27: 'Maximum doors are already configured',
  28: 'Panel door already exists',
  29: 'Invalid value',
  30: 'Door Offline',
  31: 'Photo not uploaded',
  32: 'User Name Not Found',
  33: 'Reserved for future use',
  34: 'Token Registration Failed',
  35: 'Failure — template / image not found',
  36: 'Face Not Detected',
  37: 'User Conflict — credential already enrolled to another user',
  38: 'Enroll Conflict — received image does not match previously enrolled images',
  39: 'Face Mask Detected',
  40: 'Full Face Not Visible',
  41: 'Face Not Straight',
  42: 'Duplicate PDID Entered',
  43: 'Logout process failed',
  44: 'Insufficient Rights',
};

function getResponseDesc(code) {
  return RESPONSE_CODES[code] ?? 'Unknown error';
}

function isSuccessCode(code) {
  return code === 0;
}
