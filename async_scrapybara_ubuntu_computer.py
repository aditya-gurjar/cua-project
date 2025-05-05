import asyncio
import os
import logging

from agents import AsyncComputer, Environment
from scrapybara import AsyncScrapybara
from scrapybara.core.api_error import ApiError
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure standard Python logger
logger = logging.getLogger(__name__)

BLOCKED_DOMAINS = []

CUA_KEY_TO_SCRAPYBARA_KEY = {
    "/": "slash",
    "\\": "backslash",
    "arrowdown": "Down",
    "arrowleft": "Left",
    "arrowright": "Right",
    "arrowup": "Up",
    "backspace": "BackSpace",
    "capslock": "Caps_Lock",
    "cmd": "Meta_L",
    "delete": "Delete",
    "end": "End",
    "enter": "Return",
    "esc": "Escape",
    "home": "Home",
    "insert": "Insert",
    "option": "Alt_L",
    "pagedown": "Page_Down",
    "pageup": "Page_Up",
    "tab": "Tab",
    "win": "Meta_L",
}


class AsyncScrapybaraUbuntu(AsyncComputer):
    def __init__(
        self,
        verbose: bool = False,
        instance_id: str | None = None,
        timeout_hours: float = 24,
    ):
        self.client = AsyncScrapybara(api_key=os.getenv("SCRAPYBARA_API_KEY"))
        self.instance = None
        self.instance_id = instance_id
        self.verbose = verbose
        self.timeout_hours = timeout_hours

    @property
    def environment(self) -> Environment:
        return "browser"

    @property
    def dimensions(self) -> tuple[int, int]:
        return 1024, 768

    async def initialize(self):
        if self.verbose:
            if self.instance_id:
                logger.info("Resuming Scrapybara Ubuntu instance")
            else:
                logger.info("Starting Scrapybara Ubuntu instance")

        if self.instance_id:
            self.instance = await self.client.get(self.instance_id)
            if not self.instance:
                raise Exception(f"Instance not found: {self.instance_id}")

            try:
                await self.instance.resume(timeout_hours=self.timeout_hours)
                await asyncio.sleep(5)
                if self.verbose:
                    stream_url = await self.instance.get_stream_url()
                    logger.info(
                        f"Scrapybara Ubuntu instance resumed. Stream URL: {stream_url.stream_url}"
                    )
            except ApiError as e:
                if "Instance is not paused" in str(e):
                    if self.verbose:
                        logger.info("Instance is already running, skipping resume")
                else:
                    raise
        else:
            self.instance = await self.client.start_ubuntu(
                timeout_hours=self.timeout_hours
            )
            if self.verbose:
                stream_url = await self.instance.get_stream_url()
                logger.info(
                    f"Scrapybara Ubuntu instance started. Stream URL: {stream_url.stream_url}"
                )

            # Initiate the browser
            await self.instance.browser.start()

    async def get_streaming_url(self) -> str:
        return (await self.instance.get_stream_url()).stream_url

    async def stop(self):
        if self.verbose:
            logger.info("Stopping Scrapybara Ubuntu instance")
        await self.instance.stop()
        if self.verbose:
            logger.info("Scrapybara Ubuntu instance stopped ₍ᐢ-(ｪ)-ᐢ₎")

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def screenshot(self) -> str:
        return (await self.instance.screenshot()).base_64_image

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def click(self, x: int, y: int, button: str = "left") -> None:
        button = "middle" if button == "wheel" else button
        await self.instance.computer(
            action="click_mouse",
            click_type="click",
            button=button,
            coordinates=[x, y],
            num_clicks=1,
        )

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def double_click(self, x: int, y: int) -> None:
        await self.instance.computer(
            action="click_mouse",
            click_type="click",
            button="left",
            coordinates=[x, y],
            num_clicks=2,
        )

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        await self.instance.computer(
            action="scroll",
            coordinates=[x, y],
            delta_x=scroll_x // 20,
            delta_y=scroll_y // 20,
        )

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def type(self, text: str) -> None:
        await self.instance.computer(action="type_text", text=text)

    async def wait(self, ms: int = 1000) -> None:
        await asyncio.sleep(ms / 1000)
        # Scrapybara also has `self.instance.computer(action="wait", duration=ms / 1000)`

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def move(self, x: int, y: int) -> None:
        await self.instance.computer(action="move_mouse", coordinates=[x, y])

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def keypress(self, keys: list[str]) -> None:
        mapped_keys = [
            CUA_KEY_TO_SCRAPYBARA_KEY.get(key.lower(), key.lower()) for key in keys
        ]
        await self.instance.computer(action="press_key", keys=mapped_keys)

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def drag(self, path: list[dict[str, int]]) -> None:
        if not path:
            return
        if isinstance(path[0], tuple):
            new_path = [[point[0], point[1]] for point in path]
        elif isinstance(path[0], dict):
            new_path = [[point["x"], point["y"]] for point in path]
        else:
            raise ValueError(f"Wrong path format: {path}")
        self.instance.computer(action="drag_mouse", path=new_path)

    async def pause_instance(self):
        await self.instance.pause()
