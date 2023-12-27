import requests

class HueController:
    def __init__(self, bridge_ip, user_token):
        self.bridge_ip = bridge_ip
        self.user_token = user_token

    def make_api_call_to_group(self, group_id, data):
        url = f'http://{self.bridge_ip}/api/{self.user_token}/groups/{group_id}/action'
        response = requests.put(url, json=data)
        return response.json()
    
    def make_api_call_to_light(self, light_id, data):
        url = f'http://{self.bridge_ip}/api/{self.user_token}/lights/{light_id}/state'
        response = requests.put(url, json=data)
        return response.json()

    def turn_on_light(self, light_id):
        data = {"on": True}
        return self.make_api_call_to_light(light_id, data)

    def turn_off_light(self, light_id):
        data = {"on": False}
        return self.make_api_call_to_light(light_id, data)

# Usage
BRIDGE_IP = '192.168.1.46'
USER_TOKEN = 'BplzC08YY96lJDa8IT8EjaW9KcvvU87Ubn68il7u'
group_id = 9  # Replace with your specific light ID

hue = HueController(BRIDGE_IP, USER_TOKEN)

# Turn on the light
hue.turn_on_light(group_id)

# Turn off the light
hue.turn_off_light(group_id)
