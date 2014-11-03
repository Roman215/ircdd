from zope.interface import implements
from twisted.cred import checkers, error, credentials
from ircdd import database
from twisted.python import failure
from twisted.internet import defer


# In memory storage and checking of nicknames/passwords
# If user name is not found, it adds the user to the database as unregistered
class DatabaseCredentialsChecker:
    """
    An extremely simple database credentials checker.
    """

    implements(checkers.ICredentialsChecker)

    credentialInterfaces = (credentials.IUsernamePassword,
                            credentials.IUsernameHashedPassword)

    def __init__(self, ctx):
        self.ctx = ctx
        self.db = database.IRCDDatabase(self.ctx['rdb_hostname'],
                                        self.ctx['rdb_port'])

    def addUser(self, username):
        self.db.addUser(username, '', '', False, '')

    def _cbPasswordMatch(self, matched, username):
        if matched:
            return username
        else:
            return failure.Failure(error.UnauthorizedLogin())

    def requestAvatarId(self, credentials):
        user = self.db.getUser(credentials.username)
        if user is not None:
            if user['registered'] is False:
                return str(credentials.username)
            else:
                return defer.maybeDeferred(
                    credentials.checkPassword,
                    user['password']).addCallback(
                    self._cbPasswordMatch, str(credentials.username))
        else:
            # this may need to be changed if we use encrypted credentials
            self.addUser(credentials.username)
            return self.requestAvatarId(credentials)
