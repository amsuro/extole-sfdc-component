javascript@runtime:(function () {
    var builder = context.getResponseBuilder();
    var me = context.getPerson();

    if (!me || !me.getEmail()) {
        return builder.withStatusCode(200)
            .withHeader('Content-Type', 'application/json')
            .withBody(JSON.stringify({ hasAnyData: false }))
            .build();
    }

    var SYMBOLS = { usd: '$', gbp: '£', eur: '€', jpy: '¥', percent_off: '%' };

    // ── Share links ────────────────────────────────────────────────────────
    var shareLinks = [];
    var slIter = me.createShareablesQuery().iterator();
    var sl;
    while ((sl = slIter.next()) !== null) {
        shareLinks.push({
            code:    sl.getCode(),
            link:    sl.getLink(),
            program: sl.getProgramLabel()
        });
    }

    // ── Rewards ────────────────────────────────────────────────────────────
    // Index first earned reward per friend (other_person_id) for quick join.
    var rewardsByFriendId = {};
    var rIter = me.createRewardsQuery().iterator();
    var r;
    while ((r = rIter.next()) !== null) {
        var rData     = r.getData ? r.getData() : {};
        var friendId  = rData.other_person_id || null;
        var faceValue = parseFloat(r.getFaceValue() || 0);
        var faceType  = (r.getFaceValueType() || '').toLowerCase();
        var symbol    = SYMBOLS[faceType] || faceType;
        var state     = r.getState ? r.getState() : null;
        var earned    = (state === 'SENT' || state === 'EARNED' || state === 'PAID');
        if (friendId && earned && !rewardsByFriendId[friendId]) {
            rewardsByFriendId[friendId] = {
                rewardId:      r.getRewardId(),
                state:         state,
                faceValue:     faceValue,
                faceValueType: faceType,
                amountLabel:   symbol + Math.round(faceValue),
                dateEarned:    r.getDateEarned ? (r.getDateEarned() || null) : null,
                programLabel:  r.getProgramLabel(),
                campaignId:    r.getCampaignId()
            };
        }
    }

    // ── Relationships ──────────────────────────────────────────────────────
    // role=ADVOCATE → I referred this person → they are my friend
    // role=FRIEND   → this person referred me → they are my referredBy
    var friends     = [];
    var referredBy  = null;
    var seenFriends = {};
    var personSvc   = context.getGlobalServices().personService;

    var relIter = me.createRelationshipsQuery().iterator();
    var rel;
    while ((rel = relIter.next()) !== null) {
        var role    = rel.getRole ? rel.getRole() : null;
        var otherId = rel.getOtherPersonId ? rel.getOtherPersonId() : null;
        if (!otherId) continue;

        if (role === 'ADVOCATE' && !seenFriends[otherId]) {
            seenFriends[otherId] = true;
            var reward  = rewardsByFriendId[otherId] || null;
            var relData = rel.getData ? rel.getData() : {};
            var friend  = {
                personId:    otherId,
                email:       null,
                displayName: null,
                program:     reward ? reward.programLabel : (relData.program_label || null),
                reward:      reward
            };
            try {
                var fp = personSvc.lookupPerson().withPersonId(otherId).lookup();
                friend.email = fp.getEmail() || null;
                friend.displayName = ((fp.getFirstName() || '') + ' ' + (fp.getLastName() || '')).trim()
                    || friend.email;
            } catch (e) { /* non-fatal — friend identity stays null */ }
            friends.push(friend);

        } else if (role === 'FRIEND' && !referredBy) {
            var rRelData = rel.getData ? rel.getData() : {};
            referredBy = {
                personId:    otherId,
                email:       null,
                displayName: null,
                program:     rRelData.program_label || null
            };
            try {
                var rp = personSvc.lookupPerson().withPersonId(otherId).lookup();
                referredBy.email = rp.getEmail() || null;
                referredBy.displayName = ((rp.getFirstName() || '') + ' ' + (rp.getLastName() || '')).trim()
                    || referredBy.email;
            } catch (e) {}
        }
    }

    var payload = {
        email:      me.getEmail(),
        firstName:  me.getFirstName(),
        lastName:   me.getLastName(),
        shareLinks: shareLinks,
        friends:    friends,
        referredBy: referredBy,
        hasAnyData: shareLinks.length > 0 || friends.length > 0 || referredBy !== null
    };

    return builder.withStatusCode(200)
        .withHeader('Content-Type', 'application/json')
        .withBody(JSON.stringify(payload))
        .build();
})();
