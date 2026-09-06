import requests


class MeshCom:
    def __init__(self, ip):
        self.ip = ip.strip().rstrip("/")

    def send_message(self, text, target=""):
        """Send exactly like the MeshCom node's own WebService form.

        The working dashboard request captured from the user's node uses the
        root endpoint with three query parameters:
        sendmessage=, tocall=<target>, message=<text>.
        """
        text = str(text).strip()
        target = str(target).strip()
        if not text:
            raise ValueError("Nachricht ist leer")

        # This is deliberately a GET request to /, matching the request made
        # by the working MeshCom dashboard on the user's node.
        params = [
            ("sendmessage", ""),
            ("tocall", target),
            ("message", text),
        ]
        response = requests.get(self.ip + "/", params=params, timeout=8)
        response.raise_for_status()
        content = response.content.decode("utf-8", errors="replace")
        return content, response.url, "GET"

    def get_messages(self):
        response = requests.get(
            self.ip + "/",
            params=[("getmessages", "")],
            timeout=8,
        )
        response.raise_for_status()
        return response.content.decode("utf-8", errors="replace")

