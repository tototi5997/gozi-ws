import uuid


class RoomManager:

    def __init__(self):
        self.rooms = {}
        self.clients = {}
        self.user_to_socket = {}

    ## 创建房间
    def create_room(self, room_name, creator_id, creator_name):
        room_id = str(uuid.uuid4())
        room = {
            'id': room_id,
            'name': room_name,
            "players": [{
                'id': creator_id,
                'name': creator_name,
                'status': 0,
            }],
            "game": {
                "current_turn": 0,
                "board_data": [],
                "winner": None,
                "status": 0,
            }
        }
        self.rooms[room_id] = room
        return room

    ## 加入房间
    def join_room(self, room_id, player_id, player_name):
        if (room_id not in self.rooms):
            return None, "房间不存在"

        room = self.rooms[room_id]
        if (len(room['players']) == 2):
            return None, "房间已满"

        for player in room['players']:
            if (player['id'] == player_id):
                return room, "已加入房间"

        room['players'].append({
            'id': player_id,
            'name': player_name,
            'status': 0
        })

        return room, "加入房间成功"

    ## 离开房间
    def leave_room(self, room_id, player_id):
        if (room_id not in self.rooms):
            return None, "房间不存在"

        room = self.rooms[room_id]
        room['players'] = [p for p in room['players'] if p['id'] != player_id]
        room['game']['status'] = 0

        for player in room['players']:
            if player.get('status') == 2:
                player['status'] = 0

        if not room['players']:
            del self.rooms[room_id]
            return None, "房间已解散"

        return room, None

    ## 设置玩家状态
    def set_player_status(self, room_id, player_id, status):
        if (room_id not in self.rooms):
            return None, "房间不存在"

        room = self.rooms[room_id]
        for player in room['players']:
            if player['id'] == player_id:
                player['status'] = status

    ## 获取房间列表
    def get_rooms(self):
        return list(self.rooms.values())

    ## 获取房间信息
    def get_room(self, room_id):
        return self.rooms.get(room_id)

    ## 开始游戏
    def start_game(self, room_id):
        if (room_id not in self.rooms):
            return None, "房间不存在"

        room = self.rooms[room_id]
        room['game']['status'] = 1

        players = room['players']
        for player in players:
            player['status'] = 2

    ## 落子
    def place_stone(self, room_id, board_data):
        if (room_id not in self.rooms):
            return None, "房间不存在"

        room = self.rooms[room_id]
        game = room['game']
        if (game['status'] != 1):
            return None, "游戏未开始"

        game['board_data'] = board_data
        game['current_turn'] = 1 if game['current_turn'] == 0 else 0

    ## 设置获胜者
    def set_winner(self, room_id, winner):
        if (room_id in self.rooms):
            room = self.rooms[room_id]
            game = room['game']
            game['winner'] = winner

    ## 重置游戏
    def reset_game(self, room_id):
        if (room_id in self.rooms):
            room = self.rooms[room_id]
            game = room['game']
            game['status'] = 0
            game['current_turn'] = 0
            game['board_data'] = [[0 for _ in range(15)] for _ in range(15)]
            game['winner'] = None

            players = room['players']
            for player in players:
                player['status'] = 1

    ## 注册客户端连接
    def register_client(self, websocket, user_id, user_name):
        self.clients[websocket] = {
            'id': user_id,
            'name': user_name,
        }
        self.user_to_socket[user_id] = websocket

    ## 注销客户端连接
    def unregister_client(self, websocket):
        if websocket in self.clients:
            user_id = self.clients[websocket]['id']

            # 从所有房间中移除该用户
            rooms_to_update = []
            for room_id, room in list(self.rooms.items()):
                for player in room['players']:
                    if player['id'] == user_id:
                        updated_room, _ = self.leave_room(room_id, user_id)
                        if updated_room:
                            rooms_to_update.append(updated_room)

            # 删除用户记录
            if user_id in self.user_to_socket:
                del self.user_to_socket[user_id]
            del self.clients[websocket]

            return rooms_to_update
        return []
