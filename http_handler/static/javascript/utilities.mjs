/* file used to keep functions that appear across multiple JS 
files */

export function replaceSpace(group_name) {
    let friendly_name = ' ';
    for(let i = 0; i < group_name.length; i ++) {
        if (group_name[i] == ' ') {
            friendly_name += '_';
        }
        friendly_name += group_name[i];
    }
    return friendly_name;
}