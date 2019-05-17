import asyncio

from aiohttp import web

import logging

from app.drone import get_drone_controller
from app.settings import Commands

logger = logging.getLogger(__name__)


class Connections:
    def __init__(self):
        self._web_sockets = set()

    def register(self, websocket):
        self._web_sockets.add(websocket)
        logger.info('New websocket registered')

    def unregister(self, websocket):
        self._web_sockets.remove(websocket)
        logger.info('New websocket unregistered')


class BaseWebSocketView(web.View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connections = Connections()

    async def get(self):
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)

        if not await self.is_valid(self.request, ws):
            await ws.close()
            return ws

        self.connections.register(ws)

        try:
            await self.handler(ws)
        except Exception as e:
            logger.error(e)
        finally:
            self.connections.unregister(ws)
            await ws.close()

            return ws

    async def is_valid(self, request, websocket):
        """
        :param websocket: Do some validation here.
        :return: boolean
        """
        return True

    async def handler(self, websocket):
        """
        :param websocket: Process your websocket here
        """
        pass


class CommandWebSocketView(BaseWebSocketView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dc = get_drone_controller()

    async def handler(self, websocket):
        while True:
            command = await websocket.receive_str()
            command = command.upper()

            if command == Commands.TAKEOFF:
                self.dc.takeoff()
            elif command == Commands.LAND:
                self.dc.land()
            elif command == Commands.FORWARD:
                self.dc.forward()
            elif command == Commands.BACKWARDS:
                self.dc.backward()
            elif command == Commands.UP:
                self.dc.up()
            elif command == Commands.DOWN:
                self.dc.down()
            elif command == Commands.LEFT:
                self.dc.left()
            elif command == Commands.RIGHT:
                self.dc.right()
            elif command == Commands.R_CW:
                self.dc.rotate_cw()
            elif command == Commands.R_CCW:
                self.dc.rotate_ccw()


class StatusWebSocketView(BaseWebSocketView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dc = get_drone_controller()

    async def handler(self, websocket):
        while True:
            json_to_send = {
                'battery': self.dc.get_battery(),
                'height': self.dc.get_height(),
                'speed': self.dc.get_speed(),
                'flight_time': self.dc.get_flight_time()
            }
            print("JSON: ", json_to_send)
            await websocket.send_json(json_to_send)
            await asyncio.sleep(2)