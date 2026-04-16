"""Windows media session helper - winsdk + PowerShell fallback."""
import asyncio, subprocess, json
from typing import Optional, Dict

def get_current_media() -> Optional[Dict]:
    result = _try_winsdk()
    if result is not None:
        return result
    return _try_powershell()

def _try_winsdk():
    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_async_winsdk())
        loop.close()
        return result
    except Exception:
        return None

async def _async_winsdk():
    from winsdk.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as MM,
        GlobalSystemMediaTransportControlsSessionPlaybackStatus as PBS,
    )
    manager = await MM.request_async()
    session = manager.get_current_session()
    if session is None: return None
    props = await session.try_get_media_properties_async()
    pb    = session.get_playback_info()
    if props is None: return None
    playing = pb is not None and pb.playback_status == PBS.PLAYING
    title  = (props.title or "").strip()
    artist = (props.artist or "").strip()
    if not title and not artist: return None
    return {"title": title, "artist": artist,
            "album": (props.album_title or "").strip(), "is_playing": playing}

_PS = r"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$ag = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Aw($t,$r){$m=$ag.MakeGenericMethod($r);$n=$m.Invoke($null,@($t));$n.Wait(-1)|Out-Null;$n.Result}
try {
  [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager,Windows.Media.Control,ContentType=WindowsRuntime]|Out-Null
  $m=Aw ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager])
  $s=$m.GetCurrentSession()
  if($null -eq $s){Write-Output '{}';exit}
  $p=Aw ($s.TryGetMediaPropertiesAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties])
  $pb=$s.GetPlaybackInfo()
  $pl=($pb.PlaybackStatus -eq [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionPlaybackStatus]::Playing)
  @{title=$p.Title;artist=$p.Artist;album=$p.AlbumTitle;is_playing=$pl}|ConvertTo-Json -Compress
}catch{Write-Output '{}'}
"""

def _try_powershell():
    try:
        r = subprocess.run(
            ["powershell","-NonInteractive","-NoProfile","-ExecutionPolicy","Bypass","-Command",_PS],
            capture_output=True, text=True, timeout=6,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)
        )
        raw = (r.stdout or "").strip()
        if not raw or raw == "{}": return None
        data = json.loads(raw)
        title  = (data.get("title")  or "").strip()
        artist = (data.get("artist") or "").strip()
        if not title and not artist: return None
        return {"title": title, "artist": artist,
                "album": (data.get("album") or "").strip(),
                "is_playing": bool(data.get("is_playing", False))}
    except Exception:
        return None
