import numpy as np
import faiss
from ollama import embeddings
import os
from Memory.MemoryDB import MemoryData


def embdingStr(text:str):
    print(f"开始计算向量：{text}")
    res = embeddings(
        model="nomic-embed-text",
        prompt=text
    )

    vector = np.array(res["embedding"], dtype='float32')
    vector = vector.reshape(1, -1)      # 升到二维 (1, 384)
    faiss.normalize_L2(vector)           # L2 归一化，内积=余弦相似度
    return vector

class EmbeddingDic:
    def __init__(self, faissPath ,dimension=768):
        self.faiss_path = faissPath
        if os.path.exists(self.faiss_path):
            self.index = faiss.read_index(self.faiss_path)
        else:
            base_index = faiss.IndexFlatIP(dimension)
            self.index = faiss.IndexIDMap2(base_index)

    def add_summary(self,mData:MemoryData,uid:int):
        toEmbeddingStr = ""
        if mData.summary:
            toEmbeddingStr = "[总结] " + " ".join(mData.summary) +";"
        if mData.actors:
            toEmbeddingStr += "[角色] " + " ".join(mData.actors) +";"
        if mData.objects:
            toEmbeddingStr += "[物件] " + " ".join(mData.objects) +";"
        if mData.emotions:
            toEmbeddingStr += "[情绪] " + " ".join(mData.emotions) +";"
        if mData.environment:
            toEmbeddingStr += "[环境] " + " ".join(mData.environment)
        vector = embdingStr(toEmbeddingStr)
        self._add_vector(vector,uid)

    def search_by_words(self,searchStr:str):
        query_vector = embdingStr(searchStr)
        distances, indices = self._search_vector(query_vector,5)

        uids= []
        for dis,uid in zip(distances, indices):
            uid = int(uid)
            dis = float(dis)
            if uid == -1:
                continue
            uids.append(uid)
            print(f"记忆相似度{dis} : {uid}" )
        return uids

    def _add_vector(self,vector,uid):
        vectors = np.array(vector, dtype='float32')
        if vectors.ndim == 1:
            vectors = np.expand_dims(vectors, axis=0)
        custom_ids = np.array([uid], dtype='int64')

        #L2 归一化，让内积 = 余弦相似度
        faiss.normalize_L2(vectors)

        self.index.add_with_ids(vectors, custom_ids)
        faiss.write_index(self.index, self.faiss_path)

    def _search_vector(self,query_vector, resultNum = 5 ):
        query_vector = np.array(query_vector, dtype='float32')
        if query_vector.ndim == 1:
            query_vector = np.expand_dims(query_vector, axis=0)
        distances, indices = self.index.search(query_vector, k=resultNum)

        #压成一维数组
        if hasattr(distances, 'flatten'):
            distances = distances.flatten()
        if hasattr(indices, 'flatten'):
            indices = indices.flatten()

        return distances, indices
    