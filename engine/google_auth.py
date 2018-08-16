#!/usr/bin/python
#
# Copyright 2012 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
     # http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import imaplib
import json
from optparse import OptionParser
import smtplib
import sys
import urllib
import webbrowser
from datetime import datetime, timedelta
from http_handler.settings import WEBSITE, CLIENT_ID, CLIENT_SECRET

class GoogleOauth2():
  # The URL root for accessing Google Accounts.
  GOOGLE_ACCOUNTS_BASE_URL = 'https://accounts.google.com'

  # Hardcoded dummy redirect URI for non-web apps.
  # REDIRECT_URI = 'http://murmur-dev.csail.mit.edu/login_email'
  REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
  # Record when access token is created to check whether it is expired 
  TOKEN_EXPIRED_TIME = None

  def __init__(self):
    print "OAUTH", CLIENT_ID, CLIENT_SECRET
    #pass

  def isExpired(self): 
    if not self.TOKEN_EXPIRED_TIME:
      return True

    if datetime.now() > self.TOKEN_EXPIRED_TIME:
      return True

    return False

  def setExpiredTime(self, inTime):
    TOKEN_EXPIRED_TIME = inTime

  def refresh_token(self, refresh_token):
    response = self.RefreshToken(refresh_token)

    # self.setExpiredTime( datetime.now() + timedelta(seconds=response['expires_in'] - 5) )

    print ('Access Token: %s' % response['access_token'])
    print ('Access Token Expiration Seconds: %s' % response['expires_in'])

    return response
    
  def generate_oauth2_token(self, authorization_code):
    response = self.AuthorizeTokens(CLIENT_ID, CLIENT_SECRET,
                                  authorization_code)

    self.REFRESH_TOKEN = response['refresh_token']
    self.ACCESS_TOKEN = response['access_token']
    self.setExpiredTime( datetime.now() + timedelta(seconds=response['expires_in'] - 5) )

    print ('Refresh Token: %s' % response['refresh_token'])
    print ('Access Token: %s' % response['access_token'])
    print ('Access Token Expiration Seconds: %s' % response['expires_in'])

    return response

  def AccountsUrl(self, command):
    """Generates the Google Accounts URL.
    Args:
      command: The command to execute.
    Returns:
      A URL for the given command.
    """
    return '%s/%s' % (self.GOOGLE_ACCOUNTS_BASE_URL, command)

  def UrlEscape(self, text):
    # See OAUTH 5.1 for a definition of which characters need to be escaped.
    return urllib.quote(text, safe='~-._')


  def UrlUnescape(self, text):
    # See OAUTH 5.1 for a definition of which characters need to be escaped.
    return urllib.unquote(text)


  def FormatUrlParams(self, params):
    """Formats parameters into a URL query string.
    Args:
      params: A key-value map.
    Returns:
      A URL query string version of the given parameters.
    """
    param_fragments = []
    for param in sorted(params.items(), key=lambda x: x[0]):
      param_fragments.append('%s=%s' % (param[0], self.UrlEscape(param[1])))
    return '&'.join(param_fragments)


  def GeneratePermissionUrl(self):
    """Generates the URL for authorizing access.
    This uses the "OAuth2 for Installed Applications" flow described at
    https://developers.google.com/accounts/docs/OAuth2InstalledApp
    Args:
      client_id: Client ID obtained by registering your app.
      scope: scope for access token, e.g. 'https://mail.google.com'
    Returns:
      A URL that the user should visit in their browser.
    """

    scope='https://mail.google.com/'

    params = {}
    params['client_id'] = CLIENT_ID
    params['redirect_uri'] = self.REDIRECT_URI
    params['scope'] = scope
    params['response_type'] = 'code'
    params['access_type'] = 'offline'
    return '%s?%s' % (self.AccountsUrl('o/oauth2/auth'),
                      self.FormatUrlParams(params))

  def RefreshToken(self, refresh_token):
    """Obtains a new token given a refresh token.
    See https://developers.google.com/accounts/docs/OAuth2InstalledApp#refresh
    Args:
      client_id: Client ID obtained by registering your app.
      client_secret: Client secret obtained by registering your app.
      refresh_token: A previously-obtained refresh token.
    Returns:
      The decoded response from the Google Accounts server, as a dict. Expected
      fields include 'access_token', 'expires_in', and 'refresh_token'.
    """
    params = {}
    params['client_id'] = CLIENT_ID
    params['client_secret'] = CLIENT_SECRET
    params['refresh_token'] = refresh_token
    params['grant_type'] = 'refresh_token'
    request_url = self.AccountsUrl('o/oauth2/token')

    response = urlopen(request_url, urllib.parse.urlencode(params).encode("utf-8")).read()
    return json.loads(response.decode('utf-8'))

  def AuthorizeTokens(self, client_id, client_secret, authorization_code):
    """Obtains OAuth access token and refresh token.
    This uses the application portion of the "OAuth2 for Installed Applications"
    flow at https://developers.google.com/accounts/docs/OAuth2InstalledApp#handlingtheresponse
    Args:
      client_id: Client ID obtained by registering your app.
      client_secret: Client secret obtained by registering your app.
      authorization_code: code generated by Google Accounts after user grants
          permission.
    Returns:
      The decoded response from the Google Accounts server, as a dict. Expected
      fields include 'access_token', 'expires_in', and 'refresh_token'.
    """
    params = {}
    params['client_id'] = client_id
    params['client_secret'] = client_secret
    params['code'] = authorization_code
    params['redirect_uri'] = self.REDIRECT_URI
    params['grant_type'] = 'authorization_code'
    request_url = self.AccountsUrl('o/oauth2/token')

    #response = urlopen(request_url, urllib.parse.urlencode(params).encode("utf-8")).read()
    #return json.loads(response.decode('utf-8'))

    response = urllib.urlopen(request_url, urllib.urlencode(params)).read()
    return json.loads(response)

  def GenerateOAuth2String(self, username, access_token, base64_encode=True):
    """Generates an IMAP OAuth2 authentication string.
    See https://developers.google.com/google-apps/gmail/oauth2_overview
    Args:
      username: the username (email address) of the account to authenticate
      access_token: An OAuth2 access token.
      base64_encode: Whether to base64-encode the output.
    Returns:
      The SASL argument for the OAuth2 mechanism.
    """
    auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)
    if base64_encode:
      auth_string = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
    return auth_string


  def TestImapAuthentication(self, user, auth_string):
    """Authenticates to IMAP with the given auth_string.
    Prints a debug trace of the attempted IMAP connection.
    Args:
      user: The Gmail username (full email address)
      auth_string: A valid OAuth2 string, as returned by GenerateOAuth2String.
          Must not be base64-encoded, since imaplib does its own base64-encoding.
    """
    print
    imap_conn = imaplib.IMAP4_SSL('imap.gmail.com')
    imap_conn.debug = 4
    imap_conn.authenticate('XOAUTH2', lambda x: auth_string)
    imap_conn.select('INBOX')



  def TestSmtpAuthentication(self, smtp_conn, user, auth_string):
    """Authenticates to SMTP with the given auth_string.
    Args:
      user: The Gmail username (full email address)
      auth_string: A valid OAuth2 string, not base64-encoded, as returned by
          GenerateOAuth2String.
    """
    
    print ("")
    smtp_conn.set_debuglevel(True)
    smtp_conn.ehlo(CLIENT_ID)
    smtp_conn.starttls()
    smtp_conn.docmd('AUTH', 'XOAUTH2 ' + auth_string)

  