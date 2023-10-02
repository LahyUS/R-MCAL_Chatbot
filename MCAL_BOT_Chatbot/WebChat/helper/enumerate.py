from enum import Enum

class RequestStatus(Enum):
    SUCCESS = 1
    FAIL = 2
    ERROR = 3
    
    
class ErrorCode(Enum):
    NONE = 0
    SERVER_FAIL = 11
    SERVER_ERROR = 12
    NO_LOGIN = 13
    
class MessageReactCode(Enum):
    NONE = 0
    UPVOTE = 1
    DOWNVOTE = 2
    
class StateCode(Enum):
    NONE = 0
    GENERATING = 1
    REGENERATING = 2

class ChatMode(Enum):
    NONE = 0
    GENERAL_CHAT = 1
    FILE_CHAT = 2

class ChatLimit(Enum):
    TITLE_LIMIT = 50
    