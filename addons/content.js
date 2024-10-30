function getActiveVillageDid() {
    const activeVillageLink = document.querySelector('#sidebarBoxVillagelist > div.content > ul > li.active > a');
    if (activeVillageLink) {
        const coordinatesGrid = activeVillageLink.querySelector('.coordinatesGrid');
        if (coordinatesGrid) {
            const did = coordinatesGrid.getAttribute('data-did');
            if (did) {
                console.log("Active village did:", did);
                return did;
            } else {
                console.error("Failed to extract `did` from the data-did attribute");
            }
        } else {
            console.error("coordinatesGrid element not found within active village");
        }
    } else {
        console.error("Active village link not found!");
    }
    return null;
}

async function create_farm_list() {
    const randomName = "FarmList_" + Math.random().toString(36).substring(7);  // نام تصادفی برای لیست فارم

    const activeVillageDid = getActiveVillageDid();
    if (!activeVillageDid) {
        console.error("Failed to retrieve active village did.");
        return null;
    }

    console.log("Using active village did:", activeVillageDid);

    console.log("Sending farm list creation request...");

    try {
        const createResponse = await fetch("https://tx3.speedtra.com/api/v1/ajax/raidList", {
            "credentials": "include",
            "headers": {
                "accept": "application/json, text/javascript, */*; q=0.01",
                "accept-language": "en-GB,en;q=0.9,fa-IR;q=0.8,fa;q=0.7,en-US;q=0.6",
                "authorization": "Bearer undefined",
                "content-type": "application/json; charset=UTF-8",
                "priority": "u=1, i",
                "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Linux\"",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "x-requested-with": "XMLHttpRequest",
                "x-version": "1001.2"
            },
            "referrer": "https://tx3.speedtra.com/build.php?tt=99&id=39",
            "referrerPolicy": "strict-origin-when-cross-origin",
            "body": JSON.stringify({
                "did": activeVillageDid,
                "listName": randomName,
                "method": "actionAddList",
                "t1": "0",
                "t2": "0",
                "t3": "0",
                "t4": "0",
                "t5": "5",
                "t6": "0",
                "t7": "0",
                "t8": "0",
                "t9": "0",
                "t10": "0"
            }),
            "method": "POST",
            "mode": "cors"
        });

        const createResponseData = await createResponse.json();
        console.log("Farm list creation response:", createResponseData);

        if (!createResponse.ok || !createResponseData) {
            console.error("Farm list creation failed with response data:", createResponseData);
            return null;
        }

        console.log("Farm list created successfully:", createResponseData);
        return createResponseData;
    } catch (error) {
        console.error("Error during farm list creation:", error);
        return null;
    }
}

async function find_natars_and_add_to_farm_list(my_x, my_y, min_distance, max_distance, min_population, max_population) {
    let villages = document.getElementById('villages');
    let tbl = villages.getElementsByTagName('tbody');
    let rows = tbl[0].getElementsByTagName('tr');
    let storage = [];

    for (let i = 0; i < rows.length; i++) {
        let name = rows[i].getElementsByClassName('name')[0].outerText;
        if (name.includes('شگفتی')) {
            continue;
        }

        let coords = rows[i].getElementsByClassName('coords')[0]
            .getElementsByTagName('a')[0]
            .getAttribute('href')
            .replace("/karte.php?x=", "")
            .split("&y=");
        let x = parseInt(coords[0]);
        let y = parseInt(coords[1]);
        let distance = Math.sqrt(Math.pow(my_x - x, 2) + Math.pow(my_y - y, 2));

        let inhabitants = parseInt(rows[i].getElementsByClassName('inhabitants')[0].innerText);

        if (
            distance < max_distance && distance > min_distance &&
            inhabitants >= min_population && inhabitants <= max_population
        ) {
            storage.push({ x: x.toString(), y: y.toString(), inhabitants: inhabitants });
        }
    }

    let totalNatars = storage.length;
    console.log(`Found ${totalNatars} natars.`);

    if (totalNatars > 0) {
        let numFarmLists = Math.ceil(totalNatars / 100);

        for (let i = 0; i < numFarmLists; i++) {
            let listId;
            try {
                const listData = await create_farm_list();
                if (listData && listData.listHTML) {
                    const listIdMatch = listData.listHTML.match(/data-listid="(\d+)"/);
                    if (listIdMatch && listIdMatch[1]) {
                        listId = listIdMatch[1];
                    }
                }

                if (!listId) {
                    throw new Error("Failed to extract list ID from response.");
                }
            } catch (error) {
                console.error("Failed to create farm list:", error);
                return;
            }

            let natarsToAdd = storage.slice(i * 100, (i + 1) * 100);

            for (let coord of natarsToAdd) {
                await fetch("https://tx3.speedtra.com/api/v1/ajax/raidList", {
                    "credentials": "include",
                    "headers": {
                        "accept": "application/json, text/javascript, */*; q=0.01",
                        "accept-language": "en-GB,en;q=0.9,fa-IR;q=0.8,fa;q=0.7,en-US;q=0.6",
                        "authorization": "Bearer undefined",
                        "content-type": "application/json; charset=UTF-8",
                        "priority": "u=1, i",
                        "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
                        "sec-ch-ua-mobile": "?0",
                        "sec-ch-ua-platform": "\"Linux\"",
                        "sec-fetch-dest": "empty",
                        "sec-fetch-mode": "cors",
                        "sec-fetch-site": "same-origin",
                        "x-requested-with": "XMLHttpRequest",
                        "x-version": "1001.2"
                    },
                    "referrer": "https://tx3.speedtra.com/build.php?tt=99&id=39",
                    "referrerPolicy": "strict-origin-when-cross-origin",
                    "body": JSON.stringify({
                        "method": "ActionAddSlot",
                        "listId": listId,
                        "slots": null,
                        "x": coord.x,
                        "y": coord.y,
                        "t1": "0",
                        "t2": "0",
                        "t3": "0",
                        "t4": "0",
                        "t5": "5",
                        "t6": "0",
                        "t7": "0",
                        "t8": "0",
                        "t9": "0",
                        "t10": "0",
                        "slotState": "active"
                    }),
                    "method": "POST",
                    "mode": "cors"
                });
            }

            console.log(`Added ${natarsToAdd.length} natars to farm list ID ${listId}`);
        }
    } else {
        console.log("No natars found matching the criteria.");
    }

    console.log("All natars have been added to farm lists.");
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "runScript") {
        const { my_x, my_y, min_distance, max_distance, min_population, max_population } = request.params;
        find_natars_and_add_to_farm_list(my_x, my_y, min_distance, max_distance, min_population, max_population);
        sendResponse({ status: "scriptStarted" });
    }
});
