import asyncio
import websockets
import json

from src.room_manager import RoomManager

room_manager = RoomManager()


async def handler(websocket):
    try:

        await websocket.send(
            json.dumps({
                "type": "rooms_list",
                "data": room_manager.get_rooms()
            }))

        async for message in websocket:
            try:

                data = json.loads(message)
                message_type = data.get('type')

                ## 用户注册
                if message_type == 'register':
                    user_id = data.get('data').get('user_id')
                    user_name = data.get('data').get('user_name')
                    room_manager.register_client(websocket, user_id, user_name)

                ## 获取房间列表
                if message_type == 'get_rooms':
                    await broadcast_rooms_update()

                ## 创建房间
                if message_type == 'create_room':
                    room_name = data.get('data').get('room_name')
                    creator_id = data.get('data').get('creator_id')
                    creator_name = data.get('data').get('creator_name')
                    room = room_manager.create_room(room_name, creator_id,
                                                    creator_name)
                    await broadcast_rooms_update()
                    await websocket.send(
                        json.dumps({
                            "type": "room_entered",
                            "data": room
                        }))

                ## 进入房间
                if message_type == 'join_room':
                    room_id = data.get('data').get('room_id')
                    player_id = data.get('data').get('player_id')
                    player_name = data.get('data').get('player_name')
                    room, message = room_manager.join_room(
                        room_id, player_id, player_name)

                    await broadcast_rooms_update()
                    await websocket.send(
                        json.dumps({
                            "type": "room_entered",
                            "data": room
                        }))

                ## 离开房间
                if message_type == 'leave_room':
                    room_id = data.get('data').get('room_id')
                    player_id = data.get('data').get('player_id')
                    room, message = room_manager.leave_room(room_id, player_id)

                    await broadcast_rooms_update()
                    await websocket.send(
                        json.dumps({
                            "type": "room_left",
                            "data": {
                                "message": message,
                                "room": room
                            }
                        }))

                ## 修改玩家状态
                if message_type == 'set_player_status':
                    room_id = data.get('data').get('room_id')
                    player_id = data.get('data').get('player_id')
                    status = data.get('data').get('status')
                    room_manager.set_player_status(room_id, player_id, status)

                    await notify_room_players(room_id)

                ## 开始游戏
                if message_type == 'start_game':
                    room_id = data.get('data').get('room_id')
                    room_manager.start_game(room_id)

                    await notify_room_players(room_id)

                if message_type == 'place_stone':
                    room_id = data.get('data').get('room_id')
                    board_data = data.get('data').get('board_data')
                    role = data.get('data').get('role')

                    room = room_manager.get_room(room_id)
                    game = room['game']

                    if game['current_turn'] == role:
                        room_manager.place_stone(room_id, board_data)
                        ## 通知房间内玩家，更新回合
                        await notify_room_players(room_id)

                if message_type == 'end_game':
                    room_id = data.get('data').get('room_id')
                    winner = data.get('data').get('winner')
                    room_manager.set_winner(room_id, winner)

                    await notify_winner(room_id, winner)
                    room_manager.reset_game(room_id)
                    await notify_room_players(room_id)

            except json.JSONDecodeError:
                print("无法解析消息")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        updated_rooms = room_manager.unregister_client(websocket)
        ## 如果有更新的房间才需要广播
        await broadcast_rooms_update()


async def broadcast_rooms_update():
    rooms = room_manager.get_rooms()
    message = json.dumps({'type': "room_list", "data": rooms})

    for websocket in list(room_manager.clients.keys()):
        try:
            await websocket.send(message)
        except Exception as e:
            print(f"Error sending message to client: {e}")


async def notify_room_players(room_id):
    room = room_manager.get_room(room_id)
    message = json.dumps({'type': "room_players", "data": room})
    players = room.get("players")

    for player in players:
        try:
            player_socket = room_manager.user_to_socket.get(player.get("id"))
            if player_socket:
                await player_socket.send(message)
        except Exception as e:
            print(f"Error sending message to player: {e}")


async def notify_winner(room_id, winner):
    room = room_manager.get_room(room_id)
    message = json.dumps({'type': "winner_exit", "data": winner})
    players = room.get("players")

    for player in players:
        try:
            player_socket = room_manager.user_to_socket.get(player.get("id"))
            if player_socket:
                await player_socket.send(message)
        except Exception as e:
            print(f"Error sending message to player: {e}")


async def main():
    async with websockets.serve(handler, "localhost", 8765) as server:
        print("WebSocket 服务器已启动，监听端口 8765...")
        await server.serve_forever()


def start_server():
    asyncio.run(main())


if __name__ == "__main__":
    start_server()
