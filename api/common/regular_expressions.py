BASIC_SPECIAL_CHARACTER_REGEX = r'^[\w\s!-~가-힣]+$'
ENG_OR_KOR_REGEX = r'^[a-z|A-Z|가-힣]+$'

SIZE_REGEX = r'^[a-z|A-Z|가-힣|\d|]+$'

USERNAME_REGEX = r'^[a-zA-Z\d]+$'
PASSWORD_REGEX = r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])[!-~]+$'
NAME_REGEX = r'^[가-힣]+$'
NICKNAME_REGEX = r'^[a-z\d._]+$'
MOBILE_NUMBER_REGEX = r'^01[0|1|6|7|8|9]\d{7,8}$'
PHONE_NUMBER_REGEX = r'^(0(2|3[1-3]|4[1-4]|5[1-5]|6[1-4]|70))\d{7,8}$'
ZIP_CODE_REGEX = r'^\d{5}'
