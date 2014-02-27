This is an add-on for XBMC to send events into AgoControl, receive commands like play, pause, etc. and control other devices.

You can bind some actions to your remote's keys like this:

<keymap>
  <global>
    <remote>
      <red>RunScript(script.agoxbmc, action=toggle, uuid=9bf6d81f-11ce-454f-82cd-92f808a4db25)</red>
      <green>RunScript(script.agoxbmc, action=command, command=setlevel, level=30, uuid=9bf6d81f-11ce-454f-82cd-92f808a4db25)</green>
      <blue>RunScript(script.agoxbmc, action=toggleDialog)</blue>
    </remote>
  </global>
</keymap>