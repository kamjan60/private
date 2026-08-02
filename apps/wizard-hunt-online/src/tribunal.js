"use strict";
/**
 * Capture, then judgement.
 *
 * Binding a stunned player freezes the round and puts everyone still alive
 * on a vote screen. The screen carries the accused and whoever bound them,
 * and nothing else: the evidence lives in what people say out loud, because
 * a tribunal that shows the case would be an adding machine rather than an
 * argument.
 *
 * The mage may bind and accuse like anybody else. That is deliberate -- it
 * is the only kill he has that costs him no charges, and it makes "why did
 * *you* catch him" a question worth asking.
 */

const { TRIBUNAL_VOTE_MS, TRIBUNAL_COOLDOWN, ACQUITTED_IMMUNE_MS } = require("./rules");

const VOTES = ["tak", "nie", "wstrzym"];

function makeTribunal() {
  return {
    active: null,           // { accusedId, accuserId, openedAt, votes: Map }
    lastEndedAt: -Infinity,
    immune: new Map()       // playerId -> timestamp until which they cannot be bound
  };
}

/**
 * Whether a bind may even start. Two brakes, both there to stop the round
 * turning into a mill: the room rests two minutes between tribunals, and
 * anyone the room just let go cannot be dragged back for a minute.
 */
function canBind(trib, targetId, now) {
  if (trib.active) return { ok: false, why: "Trybunał już trwa." };
  if (now - trib.lastEndedAt < TRIBUNAL_COOLDOWN) {
    const left = Math.ceil((TRIBUNAL_COOLDOWN - (now - trib.lastEndedAt)) / 1000);
    return { ok: false, why: `Trybunał stygnie jeszcze ${left} s.` };
  }
  const until = trib.immune.get(targetId) || 0;
  if (now < until) {
    return { ok: false, why: "Ten gracz został właśnie wypuszczony." };
  }
  return { ok: true };
}

function open(trib, { accusedId, accuserId, now }) {
  trib.active = { accusedId, accuserId, openedAt: now, votes: new Map() };
  return trib.active;
}

function vote(trib, voterId, choice) {
  if (!trib.active) return false;
  if (!VOTES.includes(choice)) return false;
  trib.active.votes.set(voterId, choice);
  return true;
}

const expired = (trib, now) => !!trib.active && now - trib.active.openedAt >= TRIBUNAL_VOTE_MS;

/** Everyone alive has spoken, so there is nothing left to wait for. */
function everyoneVoted(trib, livingIds) {
  if (!trib.active) return false;
  return livingIds.every((id) => trib.active.votes.has(id));
}

function tally(trib, livingIds) {
  const counts = { tak: 0, nie: 0, wstrzym: 0 };
  const cast = [];
  for (const id of livingIds) {
    const v = trib.active.votes.get(id) || "wstrzym";
    counts[v]++;
    cast.push({ id, vote: v });
  }
  return { counts, cast };
}

/**
 * Resolve the vote.
 *
 * Conviction needs a majority of the living, so abstentions and a tie both
 * release. Votes are published afterwards: how somebody voted is itself
 * evidence, and the mage voting with the crowd is a tell worth having.
 */
function resolve(trib, livingIds, now) {
  if (!trib.active) return null;
  const { accusedId, accuserId } = trib.active;
  const { counts, cast } = tally(trib, livingIds);
  const convicted = counts.tak * 2 > livingIds.length;

  trib.active = null;
  trib.lastEndedAt = now;
  if (!convicted) trib.immune.set(accusedId, now + ACQUITTED_IMMUNE_MS);

  return { accusedId, accuserId, convicted, counts, cast };
}

module.exports = { makeTribunal, canBind, open, vote, resolve, tally, expired, everyoneVoted, VOTES };
