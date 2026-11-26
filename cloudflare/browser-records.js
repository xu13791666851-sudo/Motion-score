/* Online activity records are stored in this browser, never on the public server. */
(() => {
  let database;
  const storageError = () => new Error('浏览器暂时无法保存或读取运动记录。');

  function open() {
    if (!database) {
      database = new Promise((resolve, reject) => {
        const request = indexedDB.open('motion-score-online', 1);
        request.onupgradeneeded = () => request.result.createObjectStore('cards', {keyPath: 'id'});
        request.onsuccess = () => {
          const connection = request.result;
          connection.onversionchange = () => {
            connection.close();
            database = undefined;
          };
          resolve(connection);
        };
        request.onerror = () => reject(storageError());
      }).catch(error => {
        database = undefined;
        throw error;
      });
    }
    return database;
  }

  async function transact(mode, perform) {
    const connection = await open();
    return new Promise((resolve, reject) => {
      const transaction = connection.transaction('cards', mode);
      const store = transaction.objectStore('cards');
      let result;
      let failure;
      transaction.oncomplete = () => resolve(result);
      transaction.onabort = () => reject(failure || storageError());
      perform(store, value => { result = value; }, error => {
        failure = error;
        transaction.abort();
      });
    });
  }

  async function read() {
    const entries = await transact('readonly', (store, done) => {
      const request = store.getAll();
      request.onsuccess = () => done(request.result);
    });
    return entries.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  }

  function save(data) {
    const title = data.title?.trim();
    if (!title || title.length > 80) throw new Error('卡片标题应为 1–80 字。');
    return transact('readwrite', (store, done, abort) => {
      function storeCard(previous) {
        const now = new Date().toISOString();
        const card = {...data, title, id: previous?.id || crypto.randomUUID(),
          createdAt: previous?.createdAt || now, updatedAt: now};
        const request = store.put(card);
        request.onsuccess = () => done(card);
      }

      if (!data.id) {
        storeCard();
        return;
      }
      const existing = store.get(data.id);
      existing.onsuccess = () => {
        if (!existing.result) {
          abort(new Error('在当前浏览器中找不到要更新的卡片。'));
          return;
        }
        storeCard(existing.result);
      };
    });
  }

  window.MotionScoreBrowserRecords = Object.freeze({read, save});
})();
