// Native strftime format at 30c22c is %D: month/day/two-digit-year.
// Calendar acquisition/local timezone belongs to the platform adapter.
export function formatReplayDate({year,month,day}){
 if(![year,month,day].every(Number.isInteger)||year<0||year>9999||month<1||month>12||day<1||day>31)throw Error('TH06nc replay: invalid local calendar');return String(month).padStart(2,'0')+'/'+String(day).padStart(2,'0')+'/'+String(year%100).padStart(2,'0');
}
