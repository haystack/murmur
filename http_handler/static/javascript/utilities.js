/* file used to keep functions that appear across multiple JS 
files */

// replaces spaces with underscores, replaces the replaceAll method in JS
export function replaceSpace(group_name) {
    let friendly_name = '';
    for(let i = 0; i < group_name.length; i ++) {
        let char = group_name[i]; 
        friendly_name += char == ' ' ? '_' : char;
    }
    return friendly_name;
}

