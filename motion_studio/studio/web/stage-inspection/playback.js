// Exact two-track frame commits; a late chunk may never replace a newer seek.
export function frameRequests(replay, commit, state) {
  let version = 0;
  return {
    cancel() {version++; state(false);},
    request(frame) {
      const current = ++version;
      if (replay.vertices(frame)) {state(false); replay.pin(frame); commit(frame); replay.prefetch(frame); return Promise.resolve();}
      state(true, frame);
      return replay.load(frame).then(() => {
        if (current !== version) return;
        if (!replay.vertices(frame)) throw Error('Requested source chunk was evicted before frame commit');
        replay.pin(frame); state(false); commit(frame); replay.prefetch(frame);
      }).catch(error => {if (current === version) {state(false); throw error;}});
    }
  };
}
