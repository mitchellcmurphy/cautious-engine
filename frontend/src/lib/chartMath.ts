/** Seconds since epoch, floored to the bar interval, as lightweight-charts expects. */
export function toBarTime(iso: string, intervalSec = 60): number {
  const sec = Math.floor(new Date(iso).getTime() / 1000)
  return sec - (sec % intervalSec)
}
