/* file used to keep functions that appear across multiple JS 
files */

export function replaceSpace(group_name) {
    let friendly_name = '';
    let char = '';
    for(let i = 0; i < group_name.length; i ++) {
        char_ = group_name[i]; 
        friendly_name += char == ' ' ? '_' : char;
    }
    return friendly_name;
}

