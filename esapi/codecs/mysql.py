#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
OWASP Enterprise Security API (ESAPI)
 
This file is part of the Open Web Application Security Project (OWASP)
Enterprise Security API (ESAPI) project. For details, please see
<a href="http://www.owasp.org/index.php/ESAPI">http://www.owasp.org/index.php/ESAPI</a>.
Copyright (c) 2009 - The OWASP Foundation

The ESAPI is published by OWASP under the BSD license. You should read and 
accept the LICENSE before you use, modify, and/or redistribute this software.

@author Craig Younkins (craig.younkins@owasp.org)
"""

import esapi.codecs.codec
from esapi.codecs.codec import Codec

class BadModeError(): pass

class MySQLCodec(Codec):
    """
    Implementation of the Codec interface for MySQL strings. See 
    http://mirror.yandex.ru/mirrors/ftp.mysql.com/doc/refman/5.0/en/string-syntax.html
    or more information.
    """
    
    MYSQL_MODE = 0
    ANSI_MODE = 1
   
    def __init__(self, mode):
        """
        Instantiates the MySQL codec.
        
        @param mode Either MYSQL_MODE or ANSI_MODE, changes the encoding
        """
        Codec.__init__(self)
        if mode != 0 and mode != 1:
            raise BadModeError()
        self.mode = mode
    
    def encode_character(self, immune, char):
        """
        Returns a quote-encoded character.
        """
        if char in immune:
            return char
            
        #hex_str = esapi.codecs.codec.get_hex_for_non_alphanumeric(char)
        #if hex_str is None:
        #    return char
            
        if self.mode == MySQLCodec.MYSQL_MODE:
            return self.encode_character_mysql(char)
        elif self.mode == MySQLCodec.ANSI_MODE:
            return self.encode_character_ansi(char)
        else:
            raise BadModeError()
        
        return None
        
    def encode_character_ansi(self, char):
        """
        Encodes character for ANSI SQL.
        Only the apostrophe is encoded.
        """
        
        if char == "'":
            return "''"
            
        return char
        
    def encode_character_mysql(self, char):
        """
        Encodes a character for MySQL.
        """
        lookup = {
        0x00 : "\\0",
        0x08 : "\\b",
        0x09 : "\\t",
        0x0a : "\\n",
        0x0d : "\\r",
        0x1a : "\\Z",
        0x22 : '\\"',
        0x25 : "\\%",
        0x27 : "\\'",
        0x5c : "\\\\",
        0x5f : "\\_",
        }
        
        if lookup.has_key(ord(char)):
            return lookup[ord(char)]
            
        return "\\" + char
    
    def decode_character(self, pbs):
        """
        Returns the decoded version of the character starting at index, or
        None if no decoding is possible.
        
        Formats all are legal (case sensitive)
        In ANSI_MODE '' decodes to '
        In MYSQL_MODE \\x decodes to x (or a small list of specials)
        """
        if self.mode == MySQLCodec.MYSQL_MODE:
            return self.decode_character_mysql(pbs)
        elif self.mode == MySQLCodec.ANSI_MODE:
            return self.decode_character_ansi(pbs)
        else:
            raise BadModeError()
        
        return None
        
    def decode_character_ansi(self, pbs):
        """
        Decodes the next character from an ANSI SQL escaping.
        
        @param pbs A PushbackString with the characters you want to decode
        @return a single character, decoded
        """
        pbs.mark()
        
        first = pbs.next()
        if first is None:
            pbs.reset()
            return None
            
        # if this is not an encoded character, return None
        if first != "'":
            pbs.reset()
            return None
            
        second = pbs.next()
        if second is None:
            pbs.reset()
            return None
            
        # if this is not THE encoded character, return None
        if second != "'":
            pbs.reset()
            return None
            
        return "'"
        
    def decode_character_mysql(self, pbs):
        """
        Decode the next character in the PushbackString according to MySQL mode
        
        @param a PushbackString 
        @return the next character, decoded
        """
        pbs.mark()
        
        first = pbs.next()
        if first is None:
            pbs.reset()
            return None
            
        # if this is not an encoded character, return None
        if first != "\\":
            pbs.reset()
            return None
            
        second = pbs.next()
        if second is None:
            pbs.reset()
            return None
            
        lookup = {
        "\\0" : 0x00,
        "\\b" : 0x08,
        "\\t" : 0x09,
        "\\n" : 0x0a,
        "\\r" : 0x0d,
        "\\Z" : 0x1a,
        '\\"' : 0x22,
        "\\%" : 0x25,
        "\\'" : 0x27,
        "\\\\" : 0x5c,
        "\\_" : 0x5f,
        }
        
        if lookup.has_key(first + second):
            return unichr(lookup[first + second])
            
        return second