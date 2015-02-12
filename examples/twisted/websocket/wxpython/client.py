###############################################################################
##
# Copyright (C) 2014 Tavendo GmbH
##
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
##
# http://www.apache.org/licenses/LICENSE-2.0
##
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##
###############################################################################

import wx
import json
from pprint import pprint

from autobahn.twisted.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory


class MyFrame(wx.Frame):

    """
    Our UI frame to show.

    This is taken from http://www.wxpython.org/test7.py.html and modified
    for sending events via WebSocket.
    """

    def __init__(self, app):
        # First, call the base class' __init__ method to create the frame
        wx.Frame.__init__(self, None, -1, "wxPython/Autobahn WebSocket Demo")
        self._app = app

        # Associate some events with methods of this class
        self.Bind(wx.EVT_MOVE, self.OnMove)

        # Add a panel and some controls to display the size and position
        panel = wx.Panel(self, -1)
        label1 = wx.StaticText(panel, -1, "WebSocket messages received:")
        label2 = wx.StaticText(panel, -1, "Window position:")
        self.sizeCtrl = wx.TextCtrl(panel, -1, "", style=wx.TE_READONLY)
        self.posCtrl = wx.TextCtrl(panel, -1, "", style=wx.TE_READONLY)
        self.panel = panel

        # Use some sizers for layout of the widgets
        sizer = wx.FlexGridSizer(2, 2, 5, 5)
        sizer.Add(label1)
        sizer.Add(self.sizeCtrl)
        sizer.Add(label2)
        sizer.Add(self.posCtrl)
        border = wx.BoxSizer()
        border.Add(sizer, 0, wx.ALL, 15)
        panel.SetSizerAndFit(border)
        self.Fit()

    # This method is called by the System when the window is moved,
    # because of the association above.
    def OnMove(self, event):
        pos = event.GetPosition()
        self.posCtrl.SetValue("%s, %s" % (pos.x, pos.y))

        if self._app._factory:
            proto = self._app._factory._proto
            if proto:
                evt = {'x': pos.x, 'y': pos.y}
                msg = json.dumps(evt).encode('utf8')
                proto.sendMessage(msg)


class MyClientProtocol(WebSocketClientProtocol):

    """
    Our protocol for WebSocket client connections.
    """

    def onOpen(self):
        print("WebSocket connection open.")

        # the WebSocket connection is open. we store ourselves on the
        # factory object, so that we can access this protocol instance
        # from wxPython, e.g. to use sendMessage() for sending WS msgs
        ##
        self.factory._proto = self
        self._received = 0

    def onMessage(self, payload, isBinary):
        # a WebSocket message was received. now interpret it, possibly
        # accessing the wxPython app `self.factory._app` or our
        # single UI frame `self.factory._app._frame`
        ##
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))

        self._received += 1
        frame = self.factory._app._frame
        frame.sizeCtrl.SetValue("{}".format(self._received))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))

        # the WebSocket connection is gone. clear the reference to ourselves
        # on the factory object. when accessing this protocol instance from
        # wxPython, always check if the ref is None. only use it when it's
        # not None (which means, we are actually connected)
        ##
        self.factory._proto = None


class MyClientFactory(WebSocketClientFactory):

    """
    Our factory for WebSocket client connections.
    """
    protocol = MyClientProtocol

    def __init__(self, url, app):
        WebSocketClientFactory.__init__(self, url)
        self._app = app
        self._proto = None


if __name__ == '__main__':

    import sys

    from twisted.internet import wxreactor
    wxreactor.install()
    from twisted.internet import reactor

    from twisted.python import log

    log.startLogging(sys.stdout)

    app = wx.App(False)
    app._factory = None

    app._frame = MyFrame(app)
    app._frame.Show()
    reactor.registerWxApp(app)

    app._factory = MyClientFactory("ws://localhost:9000", app)

    reactor.connectTCP("127.0.0.1", 9000, app._factory)

    reactor.run()
