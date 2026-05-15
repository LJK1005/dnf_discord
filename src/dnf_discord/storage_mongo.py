from typing import Dict, Iterable, List, Union

from pymongo import MongoClient


class MongoStorage:
    def __init__(self, uri: str, database: str) -> None:
        self._client = MongoClient(uri)
        self._db = self._client[database]

    def close(self) -> None:
        self._client.close()

    def upsert_stats(self, account_name: str, nickname: str, stats: Dict[str, int]) -> None:
        if not stats:
            return

        update_doc = {"$set": {"nickname": nickname}}
        max_doc: Dict[str, int] = {}

        for key, value in stats.items():
            if key == "ranking":
                update_doc["$set"][key] = value
            else:
                max_doc[key] = value

        if max_doc:
            update_doc["$max"] = max_doc

        collection = self._db[account_name]
        collection.update_one({"_id": nickname}, update_doc, upsert=True)

    def load_account_stats(
        self, account_name: str, nicknames: Iterable[str]
    ) -> List[Dict[str, Union[int, str, None]]]:
        collection = self._db[account_name]
        nickname_list = list(nicknames)
        docs = collection.find({"_id": {"$in": nickname_list}})
        docs_by_id = {doc["_id"]: doc for doc in docs}

        rows: List[Dict[str, Union[int, str, None]]] = []
        for nickname in nickname_list:
            doc = docs_by_id.get(nickname, {})
            rows.append(
                {
                    "nickname": nickname,
                    "ranking": doc.get("ranking"),
                    "buff_score": doc.get("buff_score"),
                    "party2": doc.get("party2"),
                    "party4": doc.get("party4"),
                }
            )

        return rows
