import re

NOT_NUMBER = re.compile("[^\d]")
SCRIPT = re.compile("AF_initDataCallback[\s\S]*?<\/script")
KEY = re.compile("(ds:.*?)'")
VALUE = re.compile("data:([\s\S]*?), sideChannel: {}}\);<\/")
REVIEWS = re.compile("\)]}'\n\n([\s\S]+)")
PERMISSIONS = re.compile("\)]}'\n\n([\s\S]+)")
SERVICE_DATA = re.compile("; var AF_dataServiceRequests[\s\S]*?; var AF_initDataChunkQueue")
